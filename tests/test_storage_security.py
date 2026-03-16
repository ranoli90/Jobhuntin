"""Tests for storage security enhancements.

Tests cover:
- S3 path validation security checks
- Local storage path resolution
- Null byte and injection character rejection
- Bucket name validation

These tests focus on the Phase 1-2 storage security fixes:
- Path traversal prevention using pathlib.Path.resolve()
- S3 pattern-based validation
- Null byte and injection prevention
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from shared.storage import (
    StorageService,
    LocalStorageService,
    _reject_path_traversal,
    _validate_s3_path,
)


class TestS3PathValidation:
    """Tests for S3 path validation security."""

    def test_validate_s3_path_accepts_valid_paths(self):
        """Valid S3 paths should be accepted."""
        # Should not raise for valid paths
        _validate_s3_path("resumes", "user123/resume.pdf")
        _validate_s3_path("documents", "folder/subfolder/file.txt")
        _validate_s3_path("avatars", "users/profile-image.png")

    def test_validate_s3_path_rejects_traversal(self):
        """Path traversal attempts should be rejected."""
        from shared.path_security import SecurityError
        
        with pytest.raises(SecurityError):
            _validate_s3_path("resumes", "../etc/passwd")
        
        with pytest.raises(SecurityError):
            _validate_s3_path("resumes", "user/../../etc/passwd")
        
        with pytest.raises(SecurityError):
            _validate_s3_path("resumes", "..%2f..%2fetc/passwd")

    def test_validate_s3_path_rejects_url_encoded_traversal(self):
        """URL-encoded traversal should be rejected."""
        from shared.path_security import SecurityError
        
        # Single encoded
        with pytest.raises(SecurityError):
            _validate_s3_path("bucket", "%2e%2e/passwd")
        
        # Double encoded
        with pytest.raises(SecurityError):
            _validate_s3_path("bucket", "%252e%252e/passwd")

    def test_validate_s3_path_rejects_null_bytes(self):
        """Null bytes in path should be rejected."""
        from shared.path_security import SecurityError
        
        with pytest.raises(SecurityError):
            _validate_s3_path("bucket", "file\x00name.txt")

    def test_validate_s3_path_rejects_newlines(self):
        """Newlines in path should be rejected."""
        from shared.path_security import SecurityError
        
        with pytest.raises(SecurityError):
            _validate_s3_path("bucket", "file\nname.txt")
        
        with pytest.raises(SecurityError):
            _validate_s3_path("bucket", "file\rname.txt")

    def test_validate_s3_path_validates_bucket(self):
        """Bucket name validation is applied."""
        from shared.path_security import SecurityError
        
        # Invalid bucket name should fail
        with pytest.raises((SecurityError, ValueError)):
            _validate_s3_path("bucket/with/slash", "file.txt")
        
        with pytest.raises((SecurityError, ValueError)):
            _validate_s3_path("..", "file.txt")


class TestLocalStoragePathTraversal:
    """Tests for local storage path traversal prevention."""

    @pytest.fixture
    def temp_storage_dir(self, tmp_path):
        """Create a temporary storage directory."""
        storage_dir = tmp_path / "storage"
        storage_dir.mkdir()
        return storage_dir

    def test_reject_path_traversal_accepts_valid_paths(self, temp_storage_dir):
        """Valid paths should be accepted."""
        result = _reject_path_traversal(temp_storage_dir, "resumes", "user123/resume.pdf")
        
        assert result.is_absolute()
        assert "resumes" in str(result)

    def test_reject_path_traversal_rejects_parent_traversal(self, temp_storage_dir):
        """Parent directory traversal should be rejected."""
        from shared.path_security import PathTraversalError
        
        with pytest.raises(PathTraversalError):
            _reject_path_traversal(temp_storage_dir, "resumes", "../etc/passwd")

    def test_reject_path_traversal_rejects_absolute_paths(self, temp_storage_dir):
        """Absolute paths should be rejected."""
        from shared.path_security import PathTraversalError
        
        with pytest.raises(PathTraversalError):
            _reject_path_traversal(temp_storage_dir, "resumes", "/etc/passwd")

    def test_reject_path_traversal_validates_bucket_name(self, temp_storage_dir):
        """Bucket name validation is applied."""
        from shared.path_security import SecurityError, PathTraversalError
        
        # Invalid bucket name
        with pytest.raises((SecurityError, ValueError)):
            _reject_path_traversal(temp_storage_dir, "bucket/with/slash", "file.txt")
        
        # Bucket with traversal attempt
        with pytest.raises((PathTraversalError, SecurityError)):
            _reject_path_traversal(temp_storage_dir, "..", "file.txt")

    def test_reject_path_traversal_resolves_symlinks(self, temp_storage_dir):
        """Symlinks should be resolved to prevent escape."""
        from shared.path_security import PathTraversalError
        
        # Create a symlink inside storage that points outside
        # First create a directory structure
        subdir = temp_storage_dir / "resumes"
        subdir.mkdir()
        
        # Create a symlink that points to parent (escape attempt)
        # Note: This test may fail on Windows if symlinks require admin
        # In that case, we skip this specific test
        import os
        try:
            symlink_path = subdir / "link_to_outside"
            if os.name != 'nt':  # Unix-like
                # Create a symlink that could be used for traversal
                os.symlink(temp_storage_dir.parent, symlink_path)
                
                # Try to access through symlink - should be caught
                with pytest.raises(PathTraversalError):
                    _reject_path_traversal(temp_storage_dir, "resumes", "link_to_outside/file.txt")
        except (OSError, NotImplementedError):
            pytest.skip("Symlink test not supported on this platform")


class TestLocalStorageService:
    """Tests for LocalStorageService implementation."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a local storage service."""
        return LocalStorageService(base_path=str(tmp_path))

    @pytest.mark.asyncio
    async def test_upload_file_creates_directory(self, storage):
        """Upload should create directories as needed."""
        data = b"test content"
        
        path = await storage.upload_file("resumes", "user123/resume.pdf", data)
        
        assert path == "resumes/user123/resume.pdf"
        assert storage.base_path.exists()

    @pytest.mark.asyncio
    async def test_upload_file_rejects_traversal(self, storage):
        """Upload should reject path traversal."""
        data = b"test content"
        
        with pytest.raises(Exception):  # PathTraversalError or similar
            await storage.upload_file("resumes", "../../etc/passwd", data)

    @pytest.mark.asyncio
    async def test_download_file_returns_content(self, storage):
        """Download should return file content."""
        data = b"test content"
        await storage.upload_file("resumes", "user123/test.txt", data)
        
        result = await storage.download_file("resumes/user123/test.txt")
        
        assert result == data

    @pytest.mark.asyncio
    async def test_download_file_rejects_traversal(self, storage):
        """Download should reject path traversal."""
        with pytest.raises(Exception):
            await storage.download_file("resumes/../../etc/passwd")

    @pytest.mark.asyncio
    async def test_generate_signed_url_returns_file_url(self, storage):
        """generate_signed_url should return file:// URL for local storage."""
        url = await storage.generate_signed_url("resumes/user123/test.txt")
        
        assert url.startswith("file://")

    @pytest.mark.asyncio
    async def test_delete_file_removes_file(self, storage):
        """delete_file should remove the file."""
        data = b"test content"
        await storage.upload_file("resumes", "user123/test.txt", data)
        
        await storage.delete_file("resumes/user123/test.txt")
        
        # File should be gone
        with pytest.raises(FileNotFoundError):
            await storage.download_file("resumes/user123/test.txt")

    @pytest.mark.asyncio
    async def test_delete_file_no_error_if_missing(self, storage):
        """delete_file should not error if file doesn't exist."""
        # Should not raise
        await storage.delete_file("resumes/nonexistent.txt")


class TestStorageServiceInterface:
    """Tests for StorageService abstract interface."""

    @pytest.mark.asyncio
    async def test_storage_service_is_abstract(self):
        """StorageService should be abstract and require implementation."""
        service = StorageService()
        
        # Should raise NotImplementedError for abstract methods
        with pytest.raises(NotImplementedError):
            await service.upload_file("bucket", "path", b"data")
        
        with pytest.raises(NotImplementedError):
            await service.generate_signed_url("path")
        
        with pytest.raises(NotImplementedError):
            await service.download_file("path")
        
        with pytest.raises(NotImplementedError):
            await service.delete_file("path")
