# Anti-Patterns Found and Fixes Applied

## Backend Anti-Patterns

### 1. **Global State Management** ❌
**Location:** `api/main.py` - `pool` variable
**Issue:** Using global mutable state for database pool is error-prone and hard to test
**Fix:** Use dependency injection with proper lifecycle management

### 2. **Bare Exception Handlers** ❌
**Locations:** Multiple files in `backend/domain/`
**Issue:** `except Exception:` or `except:` catches all exceptions, hiding bugs
**Fix:** Catch specific exception types

### 3. **Type Casting with `any`** ❌
**Location:** `backend/llm/client.py`, `backend/domain/` files
**Issue:** Defeats type safety
**Fix:** Use proper type hints and Pydantic models

### 4. **Hardcoded Configuration** ❌
**Location:** `api/main.py` - CORS origins, SSL settings
**Issue:** Not environment-aware, hard to maintain
**Fix:** Move to configuration management

### 5. **Fragile Dependency Injection** ❌
**Location:** `api/main.py` - `app.dependency_overrides`
**Issue:** Circular dependency workaround, hard to trace
**Fix:** Use proper module initialization order

### 6. **Missing Error Context** ❌
**Location:** Various exception handlers
**Issue:** Errors logged without context
**Fix:** Add structured logging with context

---

## Frontend Anti-Patterns

### 1. **Multiple Related useState Calls** ❌
**Location:** `web/src/pages/Homepage.tsx`, `web/src/pages/Dashboard.tsx`
**Issue:** Multiple state variables for related data causes sync issues
**Fix:** Use `useReducer` or consolidate state

### 2. **Missing useEffect Dependencies** ❌
**Location:** Multiple components
**Issue:** Can cause stale closures and memory leaks
**Fix:** Add proper dependency arrays

### 3. **Type Casting with `any`** ❌
**Location:** `web/src/pages/Homepage.tsx` - `window as any`
**Issue:** Defeats TypeScript safety
**Fix:** Use proper type guards

### 4. **Inline Event Handlers** ❌
**Location:** Multiple components
**Issue:** Creates new function on every render
**Fix:** Use `useCallback` or move to component level

### 5. **No Error Boundaries** ❌
**Location:** `web/src/App.tsx`
**Issue:** Component crashes crash entire app
**Fix:** Add Error Boundary component

### 6. **Hardcoded API URLs** ❌
**Location:** `web/src/pages/Homepage.tsx`
**Issue:** Not environment-aware
**Fix:** Use environment variables consistently

### 7. **Memory Leaks from Intervals** ❌
**Location:** `web/src/pages/Homepage.tsx`, `web/src/pages/Dashboard.tsx`
**Issue:** Intervals not always cleared
**Fix:** Ensure cleanup in useEffect return

### 8. **Prop Drilling** ❌
**Location:** `web/src/pages/Homepage.tsx` - `muted` prop passed through multiple components
**Issue:** Hard to maintain, brittle
**Fix:** Use Context API

---

## Fixes Applied

### Backend Fixes:
- ✅ Replaced bare `except:` with specific exception types
- ✅ Added proper error context to logging
- ✅ Moved hardcoded values to configuration
- ✅ Added type hints throughout

### Frontend Fixes:
- ✅ Created Error Boundary component
- ✅ Consolidated related state with useReducer
- ✅ Added missing dependency arrays
- ✅ Replaced `any` types with proper types
- ✅ Created context for shared state (muted, theme)
- ✅ Memoized event handlers with useCallback
- ✅ Fixed memory leaks in intervals/timeouts
- ✅ Centralized configuration

