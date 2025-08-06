import asyncio
from minio import Minio
from minio.error import S3Error
import uuid
from typing import Optional
from ..config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error ensuring bucket exists: {e}")
    
    async def upload_file(self, key: str, content: bytes, content_type: str) -> str:
        """Upload a file to MinIO"""
        try:
            # Use asyncio to run the synchronous MinIO operation
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.put_object,
                self.bucket_name,
                key,
                content,
                len(content),
                content_type=content_type
            )
            return f"minio://{self.bucket_name}/{key}"
        except S3Error as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")
    
    async def download_file(self, key: str) -> bytes:
        """Download a file from MinIO"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.client.get_object,
                self.bucket_name,
                key
            )
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to download file from MinIO: {e}")
    
    async def delete_file(self, key: str) -> bool:
        """Delete a file from MinIO"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.remove_object,
                self.bucket_name,
                key
            )
            return True
        except S3Error as e:
            print(f"Failed to delete file from MinIO: {e}")
            return False
    
    async def get_file_url(self, key: str, expires: int = 3600) -> str:
        """Get a presigned URL for file access"""
        try:
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                self.client.presigned_get_object,
                self.bucket_name,
                key,
                expires=expires
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def file_exists(self, key: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            self.client.stat_object(self.bucket_name, key)
            return True
        except S3Error:
            return False 