# Deep Profile System Implementation Progress

**Started:** 2026-02-15
**Last Updated:** 2026-02-15
**Status:** ✅ COMPLETE - Bug fixes applied, ready for commit
**Commit:** e0de0d4 (initial), bug fixes pending

---

## Bug Fixes Applied (2026-02-15)

| Bug | Status | Fix |
|-----|--------|-----|
| Missing /me/skills endpoint | ✅ Fixed | Added GET/POST endpoints in apps/api/main.py |
| Missing profile_embeddings table | ✅ Fixed | Added to migration 029, applied to DB |
| A/B test step indices wrong | ✅ Fixed | Updated indices for new 7-step flow |
| useOnboarding dependency array | ✅ Fixed | Changed STEPS -> currentSteps |
| Circular import in job_signals.py | ✅ Fixed | Using TYPE_CHECKING pattern |

---

## Implementation Order

| # | Phase | Status | Notes |
|---|-------|--------|-------|
| 1 | Database migration | ✅ Complete | All 6 tables + triggers created |
| 2 | Phase 1: Rich skill parsing (backend) | ✅ Complete | RichSkill, RichSkillsInfo, V2 prompt |
| 3 | Phase 2: Work style calibration (backend) | ✅ Complete | WorkStyleProfile, BEHAVIORAL_QUESTIONS |
| 4 | Phase 3: Skill confidence UI (new step) | ✅ Complete | SkillReviewStep created |
| 5 | Phase 4: Deep profile aggregation | ✅ Complete | DeepProfile model, completeness calc |
| 6 | Job signal extraction | ✅ Complete | JobSignals, prompts, fit calculation |
| 7 | Phase 5: Matching integration | ✅ Complete | semantic_matching.py updated |
| 8 | Testing + polish | ⏳ Pending | Needs E2E testing after deploy |

---

## Flow Order (7 Steps)

```
Welcome -> Resume -> SkillReview -> ConfirmContact -> Preferences -> WorkStyle -> Ready
```

**Step IDs:** welcome, resume, skill-review, confirm-contact, preferences, work-style, ready

**Note:** WorkStyle step (id: "work-style") currently uses CalibrationStep component for AI-generated questions. The static BEHAVIORAL_QUESTIONS from work_style.py are available for future use.

---

## Scoring Weights (UPDATED)

| Component | Weight |
|-----------|--------|
| semantic_sim | 0.30 |
| skill_match_ratio | 0.25 |
| exp_alignment | 0.15 |
| work_style_fit | 0.18 |
| trajectory_alignment | 0.12 |
| **Total** | **1.00** |

---

## Phase 1: Database Migration

### Tasks
- [x] Create migration file `029_deep_profile_system.sql`
- [x] Create migration script `scripts/run_migration.py`
- [x] Apply migration to Render database
- [x] Verify tables created correctly

### Tables Created
- `user_skills` - Rich skills with confidence, context, source
- `work_style_profiles` - Behavioral profile data (includes career_trajectory)
- `job_signals` - Extracted signals from job postings
- `deep_profiles` - Cached aggregated profile
- `job_embeddings` - Semantic matching embeddings
- Modified `users` table - Added `profile_completeness`, `has_completed_onboarding` columns

---

## Phase 2: Rich Skill Parsing (Backend)

### Tasks
- [x] Update `backend/llm/contracts.py` - Add `RichSkill`, `RichSkillsInfo`
- [x] Update `packages/backend/llm/contracts.py` - Sync changes
- [x] Add `ResumeParseResponse_V2` model
- [x] Add `RESUME_PARSE_PROMPT_V2` with deep skill extraction
- [x] Sync `packages/backend/domain/models.py`
- [x] Verify imports work

---

## Phase 3: Work Style Calibration (Backend)

### Tasks
- [x] Create `packages/backend/domain/work_style.py`
- [x] Add `WorkStyleProfile` model
- [x] Add `BEHAVIORAL_QUESTIONS` static questions
- [x] Add `CareerTrajectory` enum
- [x] Add `TRAJECTORY_QUESTION` constant
- [x] Add `compute_work_style_from_answers()` function
- [x] Copy to `backend/domain/work_style.py`
- [x] Verify imports work

### Static Behavioral Questions (6 questions)
1. blocked_dependency -> autonomy_preference
2. learning_new_tech -> learning_style
3. company_stage -> company_stage_preference
4. communication_style -> communication_style
5. work_pace -> pace_preference
6. ownership_style -> ownership_preference

---

## Phase 4: Skill Confidence UI (SkillReviewStep)

### Tasks
- [x] Create `apps/web/src/pages/app/onboarding/steps/SkillReviewStep.tsx`
- [x] Update `apps/web/src/hooks/useOnboarding.ts` - Add step to STEPS array
- [x] Update `apps/web/src/pages/app/Onboarding.tsx` - Wire up new step
- [x] Add `RichSkill` interface to `apps/web/src/types/onboarding.ts`
- [x] Show confidence badges (HIGH/MEDIUM/LOW)
- [x] Add skill edit/add/delete functionality

### Updated Flow
```
Resume -> SkillReview -> Contact -> Preferences -> Calibration -> Ready
```

---

## Phase 5: Deep Profile Aggregation

### Tasks
- [x] Create `packages/backend/domain/deep_profile.py`
- [x] Add `DeepProfile` model
- [x] Add `calculate_completeness()` function
- [x] Add helper functions for skill summaries
- [x] Copy to `backend/domain/deep_profile.py`
- [x] Verify imports work

### DeepProfile Model
- competency_graph: list[RichSkill]
- work_style: WorkStyleProfile
- trajectory: CareerTrajectory
- dealbreakers: DealbreakerConfig
- preferences: dict
- completeness_score: float

### Completeness Calculation
| Check | Points |
|-------|--------|
| resume_uploaded | 20% |
| contact_verified | 15% |
| preferences_set | 15% |
| skills_reviewed | 20% |
| work_style_calibrated | 20% |
| career_trajectory_set | 10% |
| **Total** | **100%** |

---

## Phase 6: Job Signal Extraction

### Tasks
- [x] Create `packages/backend/domain/job_signals.py`
- [x] Add `JobSignals` model
- [x] Add `JOB_SIGNALS_PROMPT` for LLM extraction
- [x] Add `compute_work_style_fit()` function
- [x] Add `compute_trajectory_alignment()` function
- [x] Copy to `backend/domain/job_signals.py`
- [x] Verify imports work

### JobSignals Model
- company_stage (early_startup, growth, enterprise)
- pace (fast, steady, methodical)
- autonomy_level (high, medium, low)
- growth_potential (ic_path, lead_path, manager_path, limited)
- team_size (small, medium, large)
- remote_culture (async_first, hybrid, onsite_culture)

---

## Phase 7: Matching Integration

### Tasks
- [x] Update `packages/backend/domain/semantic_matching.py`
- [x] Add new weights: work_style_fit (0.18), trajectory_alignment (0.12)
- [x] Add `_compute_work_style_fit()` method
- [x] Add `_compute_trajectory_alignment()` method
- [x] Update `MatchExplanation` model with new fields
- [x] Update scoring formula
- [x] Copy to `backend/domain/semantic_matching.py`
- [x] Verify imports work

### Remaining (Optional Enhancement)
- [ ] `apps/api/ai.py` - Pass deep profile to matching
- [ ] `apps/web/src/components/ui/MatchExplanation.tsx` - Show new breakdowns in UI

---

## Phase 8: Testing + Polish

### Remaining Tests
- [ ] Test resume parsing with rich skills
- [ ] Test skill save endpoint (/me/skills)
- [ ] Test work style calibration flow
- [ ] Test job signal extraction
- [ ] Test matching with new scoring
- [ ] Test profile completeness calculation
- [ ] End-to-end onboarding test

---

## Future Phases (Deferred)

| Phase | Feature | Description |
|-------|---------|-------------|
| 9 | GitHub Verification | OAuth integration, analyze repos for skill confidence boost |
| 10 | LinkedIn Verification | Cross-reference claimed experience |
| 11 | Skill Decay | Reduce confidence for skills not used recently |
| 12 | Company Signal Learning | Learn from user accept/reject patterns |

---

## Notes

- GitHub verification deferred to future phase
- Fresh start for skill data (no migration of old strings)
- Behavioral questions are static, not AI-generated
- Profile completeness unlocks "Precision Match" at 80%
- Calibration step removed - WorkStyle captures all behavioral signals
- Existing users get soft prompt: "New: Tell us your work style for better matches"
