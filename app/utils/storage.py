import logging
from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


class StorageClient:
    """
    S3-compatible storage client using aioboto3.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = aioboto3.Session()
        self.endpoint_url = self.settings.STORAGE_ENDPOINT
        self.access_key = self.settings.STORAGE_ACCESS_KEY
        self.secret_key = self.settings.STORAGE_SECRET_KEY
        self.bucket_name = self.settings.STORAGE_BUCKET_NAME

    def _get_client(self):
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="us-east-1",  # MinIO default
        )

    async def upload_file(self, file_obj: BinaryIO, object_name: str, content_type: str) -> bool:
        """
        Upload a file to the storage bucket.
        """
        try:
            async with self._get_client() as s3:
                await s3.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    object_name,
                    ExtraArgs={"ContentType": content_type},
                )
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file {object_name}: {e}")
            return False

    async def get_presigned_url(self, object_name: str, expiration: int = 900) -> str | None:
        """
        Generate a presigned URL for downloading a file.
        expiration is in seconds (default 15 minutes).
        """
        try:
            async with self._get_client() as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_name},
                    ExpiresIn=expiration,
                )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            return None

    async def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from the storage bucket.
        """
        try:
            async with self._get_client() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {object_name}: {e}")
            return False

storage_client = StorageClient()
