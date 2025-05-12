import boto3
from botocore.exceptions import ClientError
import os
from typing import Optional

class B2Manager:
    def __init__(self, bucket_name: str, bucket_id: str, key_id: str, app_key: str, endpoint: str = 's3.us-west-002.backblazeb2.com'):
        """
        Initialize B2Manager with Backblaze B2 credentials
        
        Args:
            bucket_name (str): Name of the bucket
            bucket_id (str): Bucket ID
            key_id (str): Key ID
            app_key (str): Application Key
            endpoint (str): B2 endpoint URL
        """
        self.bucket_name = bucket_name
        self.b2 = boto3.client(
            's3',
            endpoint_url=f'https://{endpoint}',
            aws_access_key_id=key_id,
            aws_secret_access_key=app_key
        )
        self.s3 = boto3.resource(
            's3',
            endpoint_url=f'https://{endpoint}',
            aws_access_key_id=key_id,
            aws_secret_access_key=app_key
        )

    def create_folder(self, folder_path: str) -> bool:
        """
        Create a folder in the bucket
        
        Args:
            folder_path (str): Path of the folder to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure folder path ends with a slash
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            # Create an empty object with the folder path as the key
            self.b2.put_object(
                Bucket=self.bucket_name,
                Key=folder_path,
                Body=''
            )
            return True
        except ClientError as e:
            print(f"Error creating folder: {e}")
            return False

    def upload_file(self, local_path: str, bucket_path: str) -> bool:
        """
        Upload a file to the bucket
        
        Args:
            local_path (str): Local path of the file to upload
            bucket_path (str): Destination path in the bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.b2.upload_file(local_path, self.bucket_name, bucket_path)
            return True
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False

    def download_file(self, bucket_path: str, local_path: str) -> bool:
        """
        Download a file from the bucket
        
        Args:
            bucket_path (str): Path of the file in the bucket
            local_path (str): Local path where to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.b2.download_file(self.bucket_name, bucket_path, local_path)
            return True
        except ClientError as e:
            print(f"Error downloading file: {e}")
            return False

    def delete_folder_recursive(self, folder_path: str) -> bool:
        """
        Delete a folder and all its contents recursively
        
        Args:
            folder_path (str): Path of the folder to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure folder path ends with a slash
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            # List all objects in the folder
            paginator = self.b2.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=folder_path)
            
            # Delete all objects in the folder
            for page in pages:
                if 'Contents' in page:
                    delete_keys = {'Objects': [{'Key': obj['Key']} for obj in page['Contents']]}
                    self.b2.delete_objects(Bucket=self.bucket_name, Delete=delete_keys)
            
            return True
        except ClientError as e:
            print(f"Error deleting folder: {e}")
            return False 