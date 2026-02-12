"""
File storage service interface for handling uploads/downloads
"""
from typing import Optional, Union
import httpx
import uuid
from pathlib import Path

class StorageService:
    """
    Abstract base class for file storage services
    """
    async def upload_file(
        self, 
        bucket: str, 
        path: str, 
        data: bytes, 
        content_type: str = "application/pdf"
    ) -> str:
        """
        Upload a file to storage and return its storage path
        """
        raise NotImplementedError
        
    async def generate_signed_url(
        self, 
        storage_path: str, 
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Generate a time-limited signed URL for accessing a stored file
        """
        raise NotImplementedError
        
    async def download_file(self, storage_path: str) -> bytes:
        """
        Download a file from storage
        """
        raise NotImplementedError

class LocalStorageService(StorageService):
    """
    Basic local filesystem storage implementation for development
    """
    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def upload_file(self, bucket: str, path: str, data: bytes, content_type: str = "application/pdf") -> str:
        """
        Save file to local filesystem
        """
        full_path = self.base_path / bucket / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        return f"{bucket}/{path}"
        
    async def generate_signed_url(self, storage_path: str, ttl_seconds: Optional[int] = None) -> str:
        """
        For local storage, just return a file:// URL
        """
        bucket, path = storage_path.split("/", 1)
        full_path = self.base_path / bucket / path
        return f"file://{full_path.absolute()}"
        
    async def download_file(self, storage_path: str) -> bytes:
        """
        Read file from local filesystem
        """
        bucket, path = storage_path.split("/", 1)
        full_path = self.base_path / bucket / path
        return full_path.read_bytes()
