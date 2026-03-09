# AI Integration Audit Report

**Date:** March 9, 2026  
**Scope:** LLM client, AI use cases, context building, validation, cost tracking, rate limiting, structured outputs

---

## Executive Summary

The codebase demonstrates **strong foundational patterns** for AI integration with retry logic, fallback models, circuit breakers, and structured outputs. However, several **critical gaps** exist in cost tracking, token counting accuracy, rate limiting consistency, and error handling robustness.

**Overall Grade: B+** (Good foundation, needs production hardening)

---

## 1. LLM Client Implementation (`packages/backend/llm/client.py`)

### ✅ Strengths

1. **Retry Logic**: ✅ Implemented with configurable retry count
   - Retries on transient errors (5xx, timeouts, connection errors)
   - Non-retryable errors (4xx, validation) fail fast

2. **Fallback Models**: ✅ Implemented
   - Configurable via `LLM_FALLBACK_MODELS` env var
   - Tries primary model first, then fallbacks in order
   - Logs fallback usage

3. **Circuit Breaker**: ✅ Implemented
   - Uses `shared.circuit_breaker` with configurable thresholds
   - Prevents cascading failures

4. **Output Validation**: ✅ Pydantic schemas
   - All contracts use Pydantic models
   - `LLMValidationError` for schema mismatches

5. **Error Handling**: ✅ Good separation
   - `LLMError` for persistent failures
   - `LLMValidationError` for schema issues
   - Circuit breaker errors handled

### ⚠️ Issues Found

#### 🔴 **CRITICAL: Inaccurate Token Counting** (Line 173-179)
```python
prompt_tokens = len(str(messages)) // 4  # Rough estimate
completion_tokens = len(str(raw_json)) // 4
```

**Problem:**
- Token counting is a **rough estimate** (dividing by 4)
- Actual token counts should come from API response
- Cost tracking depends on accurate token counts
- LLM monitoring metrics are inaccurate

**Impact:**
- Cost estimates are unreliable
- Cannot accurately track token usage
- Billing/quotas may be incorrect

**Recommendation:**
```python
# Extract actual token counts from API response
prompt_tokens = data.get("usage", {}).get("prompt_tokens", 0)
completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
total_tokens = data.get("usage", {}).get("total_tokens", 0)
```

#### 🟡 **MEDIUM: No Exponential Backoff** (Line 162-164)
```python
for attempt in range(1, self.retry_count + 2):
```

**Problem:**
- Retries happen immediately without backoff
- Can overwhelm failing services
- No jitter to prevent thundering herd

**Recommendation:**
```python
import asyncio
import random

for attempt in range(1, self.retry_count + 2):
    # ... existing code ...
    if attempt < self.retry_count + 1:
        backoff = min(2 ** attempt + random.uniform(0, 1), 30)
        await asyncio.sleep(backoff)
```

#### 🟡 **MEDIUM: Missing Request ID Tracking**
- No correlation IDs for debugging
- Hard to trace LLM calls across logs

**Recommendation:**
```python
import uuid
request_id = str(uuid.uuid4())
headers["X-Request-ID"] = request_id
logger.info("LLM call", extra={"request_id": request_id, "model": model})
```

#### 🟢 **LOW: Temperature Hardcoded to 0.0** (Line 157)
- May not be optimal for all use cases
- Consider making configurable per contract

---

## 2. AI Use Cases

### 2.1 Resume Parsing (`packages/backend/domain/resume.py`)

#### ✅ Strengths
- **Fallback parsing**: `_basic_resume_parse()` when LLM fails
- **Structured output**: Uses `ResumeParseResponse_V2` with rich skills
- **Error handling**: Catches `LLMError` and falls back gracefully
- **Metrics**: Tracks parsing method, OCR usage, file metadata

#### ⚠️ Issues

**🟡 MEDIUM: Fallback Error Handling** (Line 544-557)
```python
except Exception as fallback_exc:
    logger.error(...)
    raise HTTPException(...)
except Exception as exc:  # Duplicate except block!
    logger.error(...)
    raise HTTPException(...)
```

**Problem:**
- Duplicate exception handling blocks
- Second `except Exception` will never execute
- Dead code

**Recommendation:** Remove duplicate block

**🟡 MEDIUM: No Timeout on LLM Call** (Line 497)
- `parse_resume_to_profile()` doesn't set explicit timeout
- Relies on client default timeout
- Long-running parses can block

**Recommendation:**
```python
import asyncio
try:
    raw_profile = await asyncio.wait_for(
        parse_resume_to_profile(resume_text),
        timeout=30.0
    )
except asyncio.TimeoutError:
    # Fallback to basic parsing
```

### 2.2 Embeddings (`packages/backend/domain/embeddings.py`)

#### ✅ Strengths
- Circuit breaker protection
- Batch processing (100 items per batch)
- Timeout configured (30s)

#### ⚠️ Issues

**🟡 MEDIUM: No Retry Logic**
- Single attempt, no retries
- Transient failures cause immediate errors

**Recommendation:** Add retry logic similar to LLM client

**🟡 MEDIUM: No Token Counting**
- Embeddings API may return token usage
- Not tracked for cost monitoring

### 2.3 Resume Tailoring (`packages/backend/domain/resume_tailoring.py`)

#### ✅ Strengths
- Uses structured prompts
- ATS scoring implemented

#### ⚠️ Issues

**🟡 MEDIUM: No Response Format Validation** (Line 168)
```python
result = await self.llm.call(prompt=prompt, response_format=None)
```

**Problem:**
- No Pydantic schema for tailored summary
- Unstructured output may be inconsistent
- No validation of LLM response quality

**Recommendation:**
```python
class TailoredSummaryResponse(BaseModel):
    summary: str = Field(..., min_length=50, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)

result = await self.llm.call(
    prompt=prompt,
    response_format=TailoredSummaryResponse
)
```

### 2.4 Form Filling (`apps/worker/agent.py`)

#### ✅ Strengths
- Rate limiting (`_llm_limiter`)
- Error handling for cover letter generation

#### ⚠️ Issues

**🟡 MEDIUM: Inconsistent Error Handling** (Line 1106)
```python
except Exception as e:
    logger.warning("Cover letter generation failed...")
    return None
```

**Problem:**
- Swallows all exceptions
- No distinction between retryable/non-retryable errors
- Silent failures

**Recommendation:**
```python
except LLMError as e:
    logger.warning("Cover letter generation failed (retryable): %s", e)
    # Could retry or use template fallback
except LLMValidationError as e:
    logger.error("Cover letter validation failed: %s", e)
    return None
```

---

## 3. Context Building & Prompt Engineering

### ✅ Strengths

1. **Versioned Contracts**: `packages/backend/llm/contracts.py`
   - Clear versioning (`_V1`, `_V2`)
   - Pydantic models for structured outputs
   - Prompt templates separated from logic

2. **Input Sanitization**: `apps/api/ai.py` (Line 98-149)
   - Prompt injection protection
   - PII stripping via `strip_pii_for_llm()`
   - Length limits

3. **Rich Prompts**: V2 resume parsing includes detailed instructions

### ⚠️ Issues

**🟡 MEDIUM: Prompt Length Not Validated**
- Prompts can exceed model context windows
- No pre-validation before API call
- Risk of silent truncation

**Recommendation:**
```python
def validate_prompt_length(prompt: str, max_tokens: int = 8000) -> bool:
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = len(prompt) // 4
    if estimated_tokens > max_tokens:
        raise ValueError(f"Prompt too long: {estimated_tokens} tokens > {max_tokens}")
    return True
```

**🟡 MEDIUM: No Prompt Caching**
- Same prompts generated repeatedly
- Wasted tokens on duplicate content
- No semantic caching for similar prompts

**Recommendation:** Implement semantic cache (see `backend.domain.semantic_cache`)

**🟢 LOW: Prompt Templates Not Centralized**
- Some prompts built inline
- Hard to version and A/B test
- Consider prompt registry

---

## 4. Output Validation & Error Handling

### ✅ Strengths

1. **Pydantic Schemas**: All contracts use typed models
2. **Validation Errors**: `LLMValidationError` for schema mismatches
3. **Graceful Degradation**: Fallback responses in some endpoints

### ⚠️ Issues

**🔴 CRITICAL: Inconsistent Error Responses** (`apps/api/ai.py`)

**Problem 1: Silent Failures with Defaults** (Line 348-361)
```python
except Exception as exc:
    logger.error("Role suggestion failed: %s", exc)
    return RoleSuggestionResponse_V1(
        suggested_roles=["Software Engineer", ...],  # Hardcoded defaults
        confidence=0.5,
        reasoning="AI suggestions temporarily unavailable..."
    )
```

**Impact:**
- Users receive fake AI responses
- No indication that AI failed
- Metrics don't reflect actual failures

**Recommendation:**
```python
except LLMError as exc:
    logger.error("Role suggestion failed: %s", exc)
    raise HTTPException(
        status_code=503,
        detail="AI service temporarily unavailable. Please try again later."
    )
```

**Problem 2: Inconsistent Error Handling Across Endpoints**
- Some endpoints return defaults
- Others raise HTTPException
- No standard pattern

**Recommendation:** Create unified error handler:
```python
async def handle_llm_error(exc: Exception, endpoint: str) -> HTTPException:
    if isinstance(exc, LLMValidationError):
        return HTTPException(422, detail=f"Invalid AI response: {exc}")
    elif isinstance(exc, LLMError):
        return HTTPException(503, detail="AI service unavailable")
    else:
        logger.error(f"Unexpected error in {endpoint}: {exc}")
        return HTTPException(500, detail="Internal server error")
```

**🟡 MEDIUM: Missing Response Quality Checks**
- No validation of response quality/coherence
- LLM may return valid JSON but poor content
- No confidence thresholds

**Recommendation:**
```python
def validate_response_quality(response: BaseModel) -> bool:
    # Check for empty/default values
    # Check for reasonable content length
    # Check for confidence scores
    pass
```

---

## 5. Cost Tracking & Rate Limiting

### ✅ Strengths

1. **LLM Monitoring**: `packages/backend/domain/llm_monitoring.py`
   - Tracks latency, success rates, token usage
   - Cost estimation based on model pricing
   - Health status checks

2. **Rate Limiting**: Multiple layers
   - Per-user rate limits (`apps/api/ai.py` Line 51-59)
   - Tenant rate limiting (`packages/backend/domain/production.py`)
   - LLM rate limiter in worker (`apps/worker/agent.py` Line 83-85)

### ⚠️ Issues

**🔴 CRITICAL: Inaccurate Cost Tracking**

**Problem 1: Token Counts Are Estimates** (See Section 1)
- Cost calculations based on rough estimates
- Actual API response not used

**Problem 2: Missing Token Counts in Some Calls**
- Not all LLM calls record tokens
- Cost monitoring incomplete

**Recommendation:**
```python
# Always extract from API response
usage = data.get("usage", {})
if usage:
    get_llm_monitor().record_success(
        model=model,
        latency_seconds=duration,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
    )
```

**🟡 MEDIUM: Rate Limiting Inconsistency**

**Problem:**
- Different rate limits in different places
- `apps/api/ai.py`: 20/hour for some, 10/hour for others
- `apps/worker/agent.py`: Per-minute limits
- No centralized configuration

**Recommendation:**
```python
# Centralized rate limit config
AI_RATE_LIMITS = {
    "role_suggestion": {"max_per_hour": 20, "tier_multiplier": {"FREE": 1, "PRO": 2}},
    "cover_letter": {"max_per_hour": 10, "tier_multiplier": {"FREE": 1, "PRO": 3}},
    "resume_parse": {"max_per_hour": 50, "tier_multiplier": {"FREE": 1, "PRO": 5}},
}
```

**🟡 MEDIUM: No Cost Budgets/Quotas**
- No per-user or per-tenant cost limits
- Risk of runaway costs
- No alerts when approaching budgets

**Recommendation:**
```python
class CostBudget:
    def check_budget(self, user_id: str, estimated_cost: float) -> bool:
        monthly_spend = self.get_monthly_spend(user_id)
        budget = self.get_user_budget(user_id)
        if monthly_spend + estimated_cost > budget:
            raise HTTPException(429, "Monthly AI budget exceeded")
        return True
```

**🟢 LOW: Rate Limit Headers Missing**
- API responses don't include rate limit headers
- Clients can't implement client-side throttling
- `shared/rate_limit_headers.py` exists but not used in AI endpoints

---

## 6. Structured Outputs for Frontend

### ✅ Strengths

1. **Pydantic Models**: All contracts use typed schemas
2. **Versioned Responses**: Clear versioning strategy
3. **Rich Data Models**: `RichSkill`, `JobMatchScore_V1` with detailed fields

### ⚠️ Issues

**🟡 MEDIUM: Inconsistent Response Formats**

**Problem:**
- Some endpoints return Pydantic models directly
- Others return dicts
- Frontend must handle multiple formats

**Example:**
- `match_job()` returns `JobMatchScore_V1` ✅
- `tailor_resume()` returns `TailorResumeResponse` ✅
- But some internal functions return raw dicts

**Recommendation:** Always return Pydantic models, use `.model_dump()` for serialization

**🟡 MEDIUM: Missing Response Metadata**
- No request IDs for correlation
- No timestamps in responses
- No version info

**Recommendation:**
```python
class AIResponse(BaseModel):
    data: BaseModel
    request_id: str
    timestamp: datetime
    model_used: str
    latency_ms: float
    cache_hit: bool = False
```

**🟢 LOW: No Response Pagination**
- Batch endpoints return all results
- No pagination for large result sets
- Risk of large payloads

---

## 7. Circuit Breakers

### ✅ Strengths

1. **Implementation**: `shared/circuit_breaker.py`
   - Three states: CLOSED, OPEN, HALF_OPEN
   - Configurable thresholds
   - Per-service breakers

2. **Usage**: LLM client and embeddings use circuit breakers

### ⚠️ Issues

**🟡 MEDIUM: Circuit Breaker Configuration Not Optimized**

**Problem:**
- Default thresholds may not be optimal for LLM services
- LLM failures are expensive (cost + latency)
- Should fail fast on persistent errors

**Current Config** (Line 215):
```python
"llm": {"failure_threshold": 3, "timeout_seconds": 60.0}
```

**Recommendation:**
```python
"llm": {
    "failure_threshold": 5,  # Allow more attempts (costly to fail)
    "timeout_seconds": 30.0,  # Shorter timeout (fail fast)
    "success_threshold": 3,  # Need more successes to close
}
```

**🟡 MEDIUM: No Circuit Breaker Metrics**
- No visibility into breaker state changes
- Can't monitor breaker effectiveness
- No alerts when breakers open

**Recommendation:**
```python
# Emit metrics on state changes
incr("circuit_breaker.opened", {"service": "llm"})
incr("circuit_breaker.closed", {"service": "llm"})
```

---

## 8. Missing Features

### 🔴 **CRITICAL: No Request/Response Logging for Debugging**
- Can't debug failed prompts
- No audit trail of AI interactions
- Compliance concerns (GDPR, data retention)

**Recommendation:**
```python
class AIRequestLogger:
    async def log_request(
        self,
        prompt: str,
        model: str,
        user_id: str,
        response: BaseModel | None = None,
        error: Exception | None = None,
    ):
        # Log to secure storage (encrypted, PII-stripped)
        # Retention policy: 30 days
        # Redact sensitive data
        pass
```

### 🟡 **MEDIUM: No A/B Testing for Prompts**
- Can't test prompt improvements
- No gradual rollout
- `packages/backend/domain/ab_testing.py` exists but not used for prompts

### 🟡 **MEDIUM: No Prompt Versioning in Database**
- Prompts are code-only
- Can't rollback prompt changes
- No audit trail of prompt modifications

### 🟢 **LOW: No Streaming Support**
- All responses are synchronous
- Long-running generations block
- No progress updates for users

---

## Priority Recommendations

### Immediate (P0)

1. **Fix Token Counting** (Section 1)
   - Extract actual token counts from API responses
   - Update cost tracking to use real values

2. **Standardize Error Handling** (Section 4)
   - Remove silent failures with fake defaults
   - Create unified error handler
   - Return proper HTTP status codes

3. **Add Request/Response Logging** (Section 8)
   - Log all AI interactions for debugging
   - Implement PII redaction
   - Set retention policies

### Short-term (P1)

4. **Implement Exponential Backoff** (Section 1)
   - Add jitter to prevent thundering herd
   - Configurable backoff strategy

5. **Add Prompt Length Validation** (Section 3)
   - Validate before API calls
   - Prevent context window overflows

6. **Centralize Rate Limiting** (Section 5)
   - Single source of truth for limits
   - Per-tier multipliers
   - Rate limit headers in responses

7. **Add Cost Budgets** (Section 5)
   - Per-user monthly budgets
   - Alerts when approaching limits
   - Hard stops on budget exceeded

### Medium-term (P2)

8. **Implement Semantic Caching**
   - Cache similar prompts/responses
   - Reduce costs and latency
   - Use existing `semantic_cache` module

9. **Add Response Quality Validation**
   - Check for empty/default values
   - Confidence score thresholds
   - Reject low-quality responses

10. **Optimize Circuit Breaker Configs**
    - Tune thresholds per service
    - Add metrics and alerts
    - Monitor breaker effectiveness

### Long-term (P3)

11. **Add Streaming Support**
    - Stream long-running generations
    - Progress updates for users
    - Better UX for slow operations

12. **Implement Prompt A/B Testing**
    - Use existing `ab_testing` module
    - Gradual rollout of prompt changes
    - Measure prompt effectiveness

13. **Add Request Correlation IDs**
    - Trace requests across services
    - Better debugging and monitoring
    - Distributed tracing support

---

## Summary Statistics

| Category | Grade | Issues Found |
|----------|-------|--------------|
| LLM Client | B+ | 4 issues (1 critical, 2 medium, 1 low) |
| AI Use Cases | B | 5 issues (all medium) |
| Context Building | B+ | 3 issues (all medium) |
| Output Validation | C+ | 3 issues (1 critical, 2 medium) |
| Cost Tracking | C | 3 issues (1 critical, 2 medium) |
| Rate Limiting | B- | 2 issues (both medium) |
| Structured Outputs | B | 2 issues (both medium) |
| Circuit Breakers | B | 2 issues (both medium) |
| Missing Features | - | 4 gaps identified |

**Overall: B+** (Good foundation, needs production hardening)

---

## Conclusion

The codebase demonstrates **strong architectural patterns** for AI integration, with retry logic, fallbacks, circuit breakers, and structured outputs. However, **critical production issues** exist in:

1. **Token counting accuracy** (affects cost tracking)
2. **Error handling consistency** (affects user experience)
3. **Cost budget enforcement** (affects financial control)

Addressing the P0 items will significantly improve production readiness. The P1 and P2 items will enhance reliability, observability, and cost control.
