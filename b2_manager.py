import os
from typing import Optional
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from b2sdk.v2.exception import B2Error

class B2Manager:
    def __init__(self, bucket_name: str, bucket_id: str, key_id: str, app_key: str, endpoint: str = None):
        """
        Initialize B2Manager with Backblaze B2 credentials
        
        Args:
            bucket_name (str): Name of the bucket
            bucket_id (str): Bucket ID
            key_id (str): Application Key ID
            app_key (str): Application Key
            endpoint (str, optional): Custom B2 endpoint URL if needed
        """
        self.bucket_name = bucket_name
        self.bucket_id = bucket_id
        self.endpoint = endpoint
        
        # Setup B2 API
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        
        # Authorize account
        self.api.authorize_account("production", key_id, app_key)
        
        # Get bucket object
        self.bucket = self.api.get_bucket_by_name(bucket_name)

    def create_folder(self, folder_path: str) -> bool:
        """
        Create a folder structure in the bucket
        
        Note: B2 is an object storage system and doesn't have real folders.
        This method simply ensures the folder path exists logically in the B2 system
        by creating a small marker file.
        
        Args:
            folder_path (str): Path of the folder to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize the folder path (remove trailing slash if present)
            folder_path = folder_path.rstrip('/')
            
            # Create a marker file in the folder
            marker_path = f"{folder_path}/.b2-folder-marker"
            
            # Create an empty file as the folder marker
            self.bucket.upload_bytes(b'', marker_path)
            return True
        except B2Error as e:
            print(f"Error creating folder structure: {e}")
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
            self.bucket.upload_local_file(
                local_file=local_path,
                file_name=bucket_path
            )
            return True
        except B2Error as e:
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
            
            # Download the file
            downloaded_file = self.bucket.download_file_by_name(
                file_name=bucket_path
            )
            t = downloaded_file.save_to(local_path)
            return True
        except B2Error as e:
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
            
            # List all files in the folder
            file_versions = self.bucket.ls(folder_path, recursive=True)
            
            # Delete all files in the folder
            for file_info, _ in file_versions:
                self.bucket.delete_file_version(
                    file_id=file_info.id_,
                    file_name=file_info.file_name
                )
            
            return True
        except B2Error as e:
            print(f"Error deleting folder: {e}")
            return False 
            
    def get_file_url(self, bucket_path: str) -> str:
        """
        Gets the full B2 URL for a file in the bucket
        
        Args:
            bucket_path (str): Path of the file in the bucket
            
        Returns:
            str: The full B2 URL for the file
        """
        try:
            # Get the download URL directly from the B2 API
            download_url = self.bucket.get_download_url(bucket_path)
            return download_url
        except B2Error as e:
            print(f"Error getting file URL: {e}")
            
            # If the direct method fails, construct URL manually using endpoint
            # Fall back to the default B2 endpoint format if custom endpoint not provided
            if self.endpoint:
                endpoint = self.endpoint
            else:
                # Get the download URL info from the account info
                account_info = self.api.get_account_info()
                download_info = account_info.get_download_info()
                endpoint = download_info['downloadUrl'].split('/file/')[0]
            
            # Construct the URL
            return f"{endpoint}/file/{self.bucket_name}/{bucket_path}" 