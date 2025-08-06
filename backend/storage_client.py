import os
import uuid
from typing import Optional, Tuple
from config import config
import tempfile

class StorageClient:
    """Unified storage client for MinIO (local) and AWS S3 (production)"""
    
    def __init__(self):
        self.storage_config = config.get_storage_config()
        self.storage_type = self.storage_config['type']
        
        if self.storage_type == 'minio':
            self._init_minio_client()
        else:
            self._init_s3_client()
    
    def _init_minio_client(self):
        """Initialize MinIO client"""
        try:
            from minio import Minio
            from minio.error import S3Error
            
            self.client = Minio(
                self.storage_config['endpoint'],
                access_key=self.storage_config['access_key'],
                secret_key=self.storage_config['secret_key'],
                secure=self.storage_config['secure']
            )
            self.error_class = S3Error
            print(f"✅ MinIO client initialized: {self.storage_config['endpoint']}")
            
        except ImportError:
            raise ImportError("MinIO client not installed. Run: pip install minio")
        except Exception as e:
            raise Exception(f"Failed to initialize MinIO client: {e}")
    
    def _init_s3_client(self):
        """Initialize AWS S3 client"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.storage_config['access_key_id'],
                aws_secret_access_key=self.storage_config['secret_access_key'],
                region_name=self.storage_config['region']
            )
            self.error_class = ClientError
            print(f"✅ AWS S3 client initialized: {self.storage_config['region']}")
            
        except ImportError:
            raise ImportError("boto3 not installed. Run: pip install boto3")
        except Exception as e:
            raise Exception(f"Failed to initialize S3 client: {e}")
    
    def upload_file(self, file_path: str, original_filename: str, user_id: str) -> Tuple[str, str]:
        """
        Upload a file to storage
        
        Args:
            file_path: Local path to the file
            original_filename: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Tuple of (storage_key, storage_url)
        """
        try:
            # Generate unique storage key
            file_extension = os.path.splitext(original_filename)[1]
            storage_key = f"uploads/{user_id}/{uuid.uuid4()}{file_extension}"
            
            if self.storage_type == 'minio':
                return self._upload_to_minio(file_path, storage_key, original_filename)
            else:
                return self._upload_to_s3(file_path, storage_key, original_filename)
                
        except Exception as e:
            raise Exception(f"Failed to upload file: {e}")
    
    def _upload_to_minio(self, file_path: str, storage_key: str, original_filename: str) -> Tuple[str, str]:
        """Upload file to MinIO"""
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(self.storage_config['bucket_name']):
                self.client.make_bucket(self.storage_config['bucket_name'])
                print(f"Created MinIO bucket: {self.storage_config['bucket_name']}")
            
            # Upload file
            self.client.fput_object(
                self.storage_config['bucket_name'],
                storage_key,
                file_path,
                content_type=self._get_content_type(original_filename),
                metadata={
                    'original-filename': original_filename,
                    'user-id': user_id
                }
            )
            
            # Generate URL
            storage_url = f"http://{self.storage_config['endpoint']}/{self.storage_config['bucket_name']}/{storage_key}"
            return storage_key, storage_url
            
        except self.error_class as e:
            raise Exception(f"MinIO upload failed: {e}")
    
    def _upload_to_s3(self, file_path: str, storage_key: str, original_filename: str) -> Tuple[str, str]:
        """Upload file to AWS S3"""
        try:
            self.client.upload_file(
                file_path,
                self.storage_config['bucket_name'],
                storage_key,
                ExtraArgs={
                    'ContentType': self._get_content_type(original_filename),
                    'Metadata': {
                        'original-filename': original_filename,
                        'user-id': user_id
                    }
                }
            )
            
            storage_url = f"https://{self.storage_config['bucket_name']}.s3.amazonaws.com/{storage_key}"
            return storage_key, storage_url
            
        except self.error_class as e:
            raise Exception(f"S3 upload failed: {e}")
    
    def download_file(self, storage_key: str, local_path: str) -> bool:
        """
        Download a file from storage
        
        Args:
            storage_key: Storage key of the file
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            if self.storage_type == 'minio':
                self.client.fget_object(
                    self.storage_config['bucket_name'],
                    storage_key,
                    local_path
                )
            else:
                self.client.download_file(
                    self.storage_config['bucket_name'],
                    storage_key,
                    local_path
                )
            
            return True
            
        except Exception as e:
            print(f"Failed to download file: {e}")
            return False
    
    def delete_file(self, storage_key: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            storage_key: Storage key of the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.storage_type == 'minio':
                self.client.remove_object(self.storage_config['bucket_name'], storage_key)
            else:
                self.client.delete_object(Bucket=self.storage_config['bucket_name'], Key=storage_key)
            
            return True
            
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False
    
    def get_file_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for file access
        
        Args:
            storage_key: Storage key of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if failed
        """
        try:
            if self.storage_type == 'minio':
                url = self.client.presigned_get_object(
                    self.storage_config['bucket_name'],
                    storage_key,
                    expires=expires_in
                )
            else:
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.storage_config['bucket_name'], 'Key': storage_key},
                    ExpiresIn=expires_in
                )
            
            return url
            
        except Exception as e:
            print(f"Failed to generate presigned URL: {e}")
            return None
    
    def check_bucket_exists(self) -> bool:
        """Check if the storage bucket exists"""
        try:
            if self.storage_type == 'minio':
                return self.client.bucket_exists(self.storage_config['bucket_name'])
            else:
                self.client.head_bucket(Bucket=self.storage_config['bucket_name'])
                return True
        except Exception:
            return False
    
    def create_bucket_if_not_exists(self) -> bool:
        """Create the storage bucket if it doesn't exist"""
        try:
            if not self.check_bucket_exists():
                if self.storage_type == 'minio':
                    self.client.make_bucket(self.storage_config['bucket_name'])
                else:
                    self.client.create_bucket(
                        Bucket=self.storage_config['bucket_name'],
                        CreateBucketConfiguration={
                            'LocationConstraint': self.storage_config['region']
                        }
                    )
                print(f"Created storage bucket: {self.storage_config['bucket_name']}")
            return True
        except Exception as e:
            print(f"Failed to create storage bucket: {e}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get MIME content type based on file extension"""
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint'
        }
        file_extension = os.path.splitext(filename)[1].lower()
        return content_types.get(file_extension, 'application/octet-stream')

# Global storage client instance
storage_client = StorageClient() 