# Path Security Module

This document describes the path security system implemented in the JobHuntin codebase to prevent path traversal attacks.

## Overview

The [`shared/path_security.py`](shared/path_security.py) module provides robust protection against path traversal vulnerabilities including:
- URL encoding bypass attempts
- Double/triple encoding
- Overlong UTF-8 encoding
- Windows vs Unix path separators
- Various bypass techniques

## Core Functions

### `validate_path(base_dir, user_path, allow_absolute=False)`

Validates that a user-provided path is within a base directory.

```python
from shared.path_security import validate_path, PathTraversalError

try:
    validated_path = validate_path("/app/storage", "uploads/file.pdf")
except PathTraversalError as e:
    print(f"Security violation: {e}")
```

**Parameters:**
- `base_dir` (str|Path): The base directory that all paths must be within
- `user_path` (str): The user-provided path to validate
- `allow_absolute` (bool): If True, allow absolute paths (still validated to be within base_dir)

**Returns:** Resolved Path object

**Raises:** 
- `PathTraversalError`: If path traversal is detected
- `ValueError`: If path is invalid for other reasons

### `validate_bucket_name(bucket)`

Validates a bucket/container name for safety.

```python
from shared.path_security import validate_bucket_name

bucket = validate_bucket_name("user-uploads")  # Returns validated name
bucket = validate_bucket_name("../../../etc")   # Raises ValueError
```

### `validate_storage_path(base_dir, bucket, path)`

Validates a storage path consisting of bucket and path components.

```python
from shared.path_security import validate_storage_path

path = validate_storage_path("/app/storage", "uploads", "user files/document.pdf")
```

### `is_path_safe(base_dir, user_path)`

Boolean check without raising exceptions.

```python
from shared.path_security import is_path_safe

if is_path_safe("/app/storage", request.path):
    # Process file
else:
    # Reject request
```

## Detection Patterns

The module detects the following path traversal patterns:

### Raw Patterns
- `../` at start of path
- `/../` anywhere in path
- `..\` on Windows
- `..` at end of path

### URL Encoded
- `%2e%2e` - Double encoded `..`
- `%2e.` - Partially encoded
- `.%2e` - Partially encoded

### Double Encoded
- `%252e` - Double encoded `.`
- `%252e%252e` - Double encoded `..`

### Overlong UTF-8
- `%c0%ae` - Overlong encoding of `.`
- `%c1%9c` - Overlong encoding of `\`
- `%c0%af` - Overlong encoding of `/`

## Usage in API Endpoints

### File Upload Validation

```python
from fastapi import APIRouter, UploadFile
from shared.path_security import validate_storage_path, PathTraversalError

router = APIRouter()

@router.post("/upload")
async def upload_file(bucket: str, path: str, file: UploadFile):
    try:
        validated_path = validate_storage_path(
            base_dir=settings.storage_path,
            bucket=bucket,
            path=path
        )
        # Proceed with file save
    except PathTraversalError:
        raise HTTPException(status_code=400, detail="Invalid path")
```

### Static File Serving

```python
from fastapi import APIRouter, HTTPException
from shared.path_security import validate_path, is_path_safe

router = APIRouter()

@router.get("/files/{filepath:path}")
async def get_file(filepath: str):
    if not is_path_safe("/app/public", filepath):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Serve file
```

## Best Practices

### DO
- ✅ Always validate user-provided paths before file operations
- ✅ Use `is_path_safe` for simple boolean checks
- ✅ Log traversal attempts for security monitoring
- ✅ Combine with proper authentication/authorization
- ✅ Use allowlist approach for permitted paths

### DON'T
- ❌ Trust user input without validation
- ❌ Only check for `..` in the path
- ❌ Forget to decode before checking (encoded bypasses)
- ❌ Use string manipulation alone (use Path.resolve())
- ❌ Allow absolute paths unless explicitly needed

## Testing

Run path security tests:

```bash
PYTHONPATH=apps:packages:. pytest tests/test_path_security.py -v
```

## Exception Handling

```python
from shared.path_security import PathTraversalError

@app.exception_handler(PathTraversalError)
async def path_traversal_exception_handler(request, exc):
    logger.warning(f"Path traversal attempt: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid path"}
    )
```
