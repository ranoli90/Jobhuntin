# Best Practices Guide - Post Anti-Pattern Fixes

## Frontend Best Practices

### 1. State Management
✅ **DO:**
```typescript
// Use Context for shared state
const { muted, toggleMute } = useAppContext();

// Use useReducer for complex state
const [state, dispatch] = useReducer(reducer, initialState);

// Use React Query for server state
const { data, isLoading } = useQuery(['key'], fetchFn);
```

❌ **DON'T:**
```typescript
// Don't use multiple related useState calls
const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
const [confirmPassword, setConfirmPassword] = useState("");

// Don't prop drill
<Component prop1={prop1} prop2={prop2} prop3={prop3} />
```

### 2. Effects and Cleanup
✅ **DO:**
```typescript
useEffect(() => {
  let mounted = true;

  const fetchData = async () => {
    try {
      const data = await api.get('/data');
      if (mounted) {
        setData(data);
      }
    } catch (error) {
      if (mounted) {
        setError(error);
      }
    }
  };

  fetchData();

  return () => {
    mounted = false;
  };
}, [dependencies]); // Always include dependencies
```

❌ **DON'T:**
```typescript
// Missing dependencies
useEffect(() => {
  setInterval(() => {
    // ...
  }, 1000);
}, []); // Missing cleanup!

// Stale closures
useEffect(() => {
  const handler = () => console.log(value); // Stale value
  window.addEventListener('resize', handler);
  // Missing cleanup
}, []);
```

### 3. Type Safety
✅ **DO:**
```typescript
// Use proper types
interface User {
  id: string;
  name: string;
  email: string;
}

const user: User = { id: '1', name: 'John', email: 'john@example.com' };

// Use type guards
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    'email' in obj
  );
}
```

❌ **DON'T:**
```typescript
// Don't use any
const user: any = data;

// Don't cast to any
const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();

// Don't ignore TypeScript errors
// @ts-ignore
const value = someUnsafeOperation();
```

### 4. Event Handlers
✅ **DO:**
```typescript
// Memoize event handlers
const handleClick = useCallback(() => {
  navigate('/path');
}, [navigate]);

const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
}, []);

<button onClick={handleClick}>Click me</button>
```

❌ **DON'T:**
```typescript
// Inline handlers create new function on every render
<button onClick={() => navigate('/path')}>Click me</button>

// Handlers without dependencies
const handleClick = () => {
  console.log(value); // Stale value!
};
```

### 5. Error Handling
✅ **DO:**
```typescript
// Use Error Boundary for component errors
<ErrorBoundary>
  <App />
</ErrorBoundary>

// Handle async errors
try {
  const data = await api.get('/data');
  setData(data);
} catch (error) {
  if (error instanceof NetworkError) {
    setError('Network error');
  } else if (error instanceof ValidationError) {
    setError('Validation error');
  } else {
    setError('Unknown error');
  }
}
```

❌ **DON'T:**
```typescript
// Don't ignore errors
api.get('/data').then(setData);

// Don't use bare catch
try {
  // ...
} catch {
  // Silently fail
}

// Don't catch all errors the same way
try {
  // ...
} catch (error) {
  console.log('Error:', error);
}
```

### 6. Configuration
✅ **DO:**
```typescript
// Use centralized config
import { config } from './config';

const apiUrl = config.api.baseUrl;
const emailRegex = config.validation.emailRegex;

// Validate config on startup
const errors = validateConfig();
if (errors.length > 0) {
  throw new Error(`Configuration errors: ${errors.join(', ')}`);
}
```

❌ **DON'T:**
```typescript
// Don't hardcode values
const API_URL = "https://api.example.com";

// Don't scatter config throughout codebase
const baseUrl = import.meta.env.VITE_API_URL;
const timeout = 30000;
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
```

---

## Backend Best Practices

### 1. Dependency Injection
✅ **DO:**
```python
# Use FastAPI dependencies
async def get_pool() -> asyncpg.Pool:
    return _pool_manager.pool

@app.get("/data")
async def get_data(db: asyncpg.Pool = Depends(get_pool)):
    # Use injected dependency
    async with db.acquire() as conn:
        return await conn.fetch("SELECT * FROM data")
```

❌ **DON'T:**
```python
# Don't use global state
pool: asyncpg.Pool | None = None

@app.get("/data")
async def get_data():
    global pool
    # Use global pool
```

### 2. Exception Handling
✅ **DO:**
```python
# Catch specific exceptions
try:
    result = await db.fetch(query)
except asyncpg.PostgresError as exc:
    logger.error("Database error: %s", exc)
    raise HTTPException(status_code=500, detail="Database error")
except ValueError as exc:
    logger.error("Invalid value: %s", exc)
    raise HTTPException(status_code=400, detail="Invalid input")
except Exception as exc:
    logger.error("Unexpected error: %s", exc)
    raise
```

❌ **DON'T:**
```python
# Don't catch all exceptions
try:
    result = await db.fetch(query)
except Exception:
    pass

# Don't ignore errors
try:
    result = await db.fetch(query)
except:
    return None
```

### 3. Logging
✅ **DO:**
```python
# Use structured logging with context
logger.info("User created", extra={
    "user_id": user_id,
    "tenant_id": tenant_id,
    "email": email,
})

logger.error("Failed to process application", extra={
    "application_id": app_id,
    "error": str(exc),
    "attempt": attempt,
})
```

❌ **DON'T:**
```python
# Don't log without context
logger.info("Error occurred")

# Don't log sensitive data
logger.info(f"User password: {password}")

# Don't use print for logging
print("Something happened")
```

### 4. Type Hints
✅ **DO:**
```python
# Use type hints for all functions
async def get_user(
    user_id: str,
    db: asyncpg.Connection,
) -> dict[str, Any]:
    """Get user by ID."""
    row = await db.fetchrow(
        "SELECT * FROM users WHERE id = $1",
        user_id,
    )
    return dict(row) if row else None

# Use Pydantic models
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
```

❌ **DON'T:**
```python
# Don't omit type hints
def get_user(user_id, db):
    # ...

# Don't use Any unnecessarily
def process_data(data: Any) -> Any:
    # ...
```

### 5. Resource Management
✅ **DO:**
```python
# Use context managers for resource cleanup
async with db.acquire() as conn:
    async with conn.transaction():
        # Do work
        pass
# Connection automatically returned to pool

# Use try/finally for cleanup
try:
    resource = acquire_resource()
    # Use resource
finally:
    resource.close()
```

❌ **DON'T:**
```python
# Don't forget to close resources
conn = await db.acquire()
# Do work
# Forgot to release!

# Don't ignore cleanup
try:
    resource = acquire_resource()
    # Use resource
except:
    pass
# Resource not cleaned up
```

### 6. Configuration
✅ **DO:**
```python
# Use environment-based configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

❌ **DON'T:**
```python
# Don't hardcode configuration
DATABASE_URL = "postgresql://user:pass@localhost/db"
API_KEY = "secret-key-123"

# Don't mix configuration with code
if os.getenv("ENV") == "prod":
    DATABASE_URL = "prod-url"
else:
    DATABASE_URL = "dev-url"
```

---

## Testing Best Practices

### Frontend
```typescript
// Test hooks in isolation
import { renderHook, act } from '@testing-library/react';

test('useAuth initializes correctly', async () => {
  const { result } = renderHook(() => useAuth());
  
  expect(result.current.loading).toBe(true);
  
  await act(async () => {
    // Wait for initialization
  });
  
  expect(result.current.loading).toBe(false);
});

// Test components with ErrorBoundary
test('ErrorBoundary catches errors', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };
  
  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );
  
  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
});
```

### Backend
```python
# Test with proper fixtures
@pytest.fixture
async def db_pool():
    pool = await asyncpg.create_pool(TEST_DATABASE_URL)
    yield pool
    await pool.close()

@pytest.mark.asyncio
async def test_get_user(db_pool):
    async with db_pool.acquire() as conn:
        user = await get_user("user-1", conn)
        assert user is not None
        assert user["id"] == "user-1"

# Test error handling
@pytest.mark.asyncio
async def test_get_user_not_found(db_pool):
    async with db_pool.acquire() as conn:
        user = await get_user("nonexistent", conn)
        assert user is None
```

---

## Code Review Checklist

- [ ] No global mutable state
- [ ] All exceptions are specific types
- [ ] All useEffect has dependency array
- [ ] All async operations have cleanup
- [ ] No `any` type casts
- [ ] Error boundaries in place
- [ ] Configuration centralized
- [ ] Logging includes context
- [ ] Type hints on all functions
- [ ] Resources properly cleaned up
- [ ] No hardcoded values
- [ ] Tests cover error cases

---

## Resources

- [React Hooks Best Practices](https://react.dev/reference/react)
- [TypeScript Best Practices](https://www.typescriptlang.org/docs/handbook/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Error Handling in React](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)

