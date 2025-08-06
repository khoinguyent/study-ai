import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
import uuid
from typing import Optional, Tuple

load_dotenv()

class S3Client:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'study-ai-documents')
        
    def upload_file(self, file_path: str, original_filename: str, user_id: str) -> Tuple[str, str]:
        """
        Upload a file to S3
        
        Args:
            file_path: Local path to the file
            original_filename: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Tuple of (s3_key, s3_url)
        """
        try:
            # Generate unique S3 key
            file_extension = os.path.splitext(original_filename)[1]
            s3_key = f"uploads/{user_id}/{uuid.uuid4()}{file_extension}"
            
            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': self._get_content_type(file_extension),
                    'Metadata': {
                        'original-filename': original_filename,
                        'user-id': user_id
                    }
                }
            )
            
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            return s3_key, s3_url
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {e}")
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 key of the file
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
            
        except ClientError as e:
            print(f"Failed to download file from S3: {e}")
            return False
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            s3_key: S3 key of the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
            
        except ClientError as e:
            print(f"Failed to delete file from S3: {e}")
            return False
    
    def get_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for file access
        
        Args:
            s3_key: S3 key of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            print(f"Failed to generate presigned URL: {e}")
            return None
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get MIME content type based on file extension"""
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def check_bucket_exists(self) -> bool:
        """Check if the S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
    
    def create_bucket_if_not_exists(self) -> bool:
        """Create the S3 bucket if it doesn't exist"""
        try:
            if not self.check_bucket_exists():
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': os.getenv('AWS_REGION', 'us-east-1')
                    }
                )
                print(f"Created S3 bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            print(f"Failed to create S3 bucket: {e}")
            return False

# Global S3 client instance
s3_client = S3Client() 