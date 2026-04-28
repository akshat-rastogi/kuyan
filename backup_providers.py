"""
KUYAN - Backup Providers Module
Licensed under MIT License - see LICENSE file for details

This module provides abstraction for multiple cloud backup providers.
"""

import json
import os
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import requests
import streamlit as st
from msal import PublicClientApplication

from database import Database


class BackupProvider(ABC):
    """Abstract base class for backup providers"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the provider name"""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate user, return True if successful"""
        pass
    
    @abstractmethod
    def sign_out(self):
        """Sign out user"""
        pass
    
    @abstractmethod
    def get_user_info(self) -> Optional[str]:
        """Get authenticated user info (email/username)"""
        pass
    
    @abstractmethod
    def backup(self, db: Database) -> Dict:
        """Backup database, return metadata dict"""
        pass
    
    @abstractmethod
    def restore(self, db: Database):
        """Restore database from backup"""
        pass


class OneDriveProvider(BackupProvider):
    """Microsoft OneDrive backup provider"""
    
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    APP_FOLDER = "KUYAN"
    BACKUP_FILE = "kuyan.db"
    SCOPES = ["Files.ReadWrite", "User.Read"]
    DEFAULT_CLIENT_ID = "04f0c124-f2bc-4f59-8241-bf6df9866bbd"
    
    def __init__(self):
        self.client_id = st.session_state.get("onedrive_client_id", self.DEFAULT_CLIENT_ID)
    
    def get_name(self) -> str:
        return "OneDrive"
    
    def is_authenticated(self) -> bool:
        return st.session_state.get("onedrive_account") is not None
    
    def authenticate(self) -> bool:
        """Start Microsoft device code flow"""
        try:
            app = PublicClientApplication(
                self.client_id,
                authority="https://login.microsoftonline.com/consumers"
            )
            flow = app.initiate_device_flow(scopes=self.SCOPES)
            
            if "user_code" not in flow:
                raise RuntimeError("Could not start Microsoft device sign-in flow.")
            
            st.info(flow["message"])
            token_result = app.acquire_token_by_device_flow(flow)
            
            if "access_token" not in token_result:
                error_description = token_result.get("error_description", "Unknown sign-in error")
                raise RuntimeError(error_description)
            
            st.session_state.onedrive_token = token_result
            account = app.get_accounts()
            if account:
                st.session_state.onedrive_account = account[0]
            else:
                st.session_state.onedrive_account = {
                    "username": token_result.get("id_token_claims", {}).get(
                        "preferred_username", "Microsoft account"
                    )
                }
            return True
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            return False
    
    def sign_out(self):
        st.session_state.pop("onedrive_token", None)
        st.session_state.pop("onedrive_account", None)
    
    def get_user_info(self) -> Optional[str]:
        account = st.session_state.get("onedrive_account")
        return account.get("username") if account else None
    
    def _get_access_token(self) -> str:
        """Get valid access token"""
        token_result = st.session_state.get("onedrive_token")
        if not token_result or "access_token" not in token_result:
            raise RuntimeError("Please sign in to OneDrive first.")
        
        expires_at = token_result.get("expires_at")
        if expires_at and float(expires_at) > datetime.now(timezone.utc).timestamp() + 60:
            return token_result["access_token"]
        
        # Try to refresh token
        app = PublicClientApplication(
            self.client_id,
            authority="https://login.microsoftonline.com/consumers"
        )
        accounts = app.get_accounts()
        if accounts:
            refreshed = app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if refreshed and "access_token" in refreshed:
                st.session_state.onedrive_token = refreshed
                st.session_state.onedrive_account = accounts[0]
                return refreshed["access_token"]
        
        raise RuntimeError("OneDrive session expired. Please sign in again.")
    
    def backup(self, db: Database) -> Dict:
        """Backup database to OneDrive"""
        access_token = self._get_access_token()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = os.path.join(temp_dir, self.BACKUP_FILE)
            db.create_backup_snapshot(snapshot_path)
            
            with open(snapshot_path, "rb") as db_file:
                response = requests.put(
                    f"{self.GRAPH_BASE_URL}/me/drive/root:/{self.APP_FOLDER}/{self.BACKUP_FILE}:/content",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/octet-stream",
                    },
                    data=db_file.read(),
                    timeout=120,
                )
        
        if response.status_code not in (200, 201):
            raise RuntimeError(self._parse_error(response))
        
        item = response.json()
        return {
            "name": item.get("name"),
            "size": item.get("size"),
            "modified": item.get("lastModifiedDateTime"),
        }
    
    def restore(self, db: Database):
        """Restore database from OneDrive"""
        access_token = self._get_access_token()
        
        response = requests.get(
            f"{self.GRAPH_BASE_URL}/me/drive/root:/{self.APP_FOLDER}/{self.BACKUP_FILE}:/content",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=120,
            allow_redirects=True,
        )
        
        if response.status_code != 200:
            raise RuntimeError(self._parse_error(response))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = os.path.join(temp_dir, self.BACKUP_FILE)
            with open(download_path, "wb") as restored_file:
                restored_file.write(response.content)
            
            db.replace_database_file(download_path)
    
    def _parse_error(self, response: requests.Response) -> str:
        """Extract error message from response"""
        try:
            payload = response.json()
            return payload.get("error", {}).get("message", f"HTTP {response.status_code}")
        except (ValueError, json.JSONDecodeError):
            return f"HTTP {response.status_code}: {response.text[:200]}"


class GoogleDriveProvider(BackupProvider):
    """Google Drive backup provider"""
    
    APP_FOLDER = "KUYAN"
    BACKUP_FILE = "kuyan.db"
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    
    def get_name(self) -> str:
        return "Google Drive"
    
    def is_authenticated(self) -> bool:
        return st.session_state.get("gdrive_credentials") is not None
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive using OAuth2"""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            import pickle
            
            creds = None
            # Check if we have stored credentials
            if "gdrive_credentials" in st.session_state:
                creds = st.session_state.gdrive_credentials
            
            # If no valid credentials, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Need client_secrets.json file
                    client_config = st.session_state.get("gdrive_client_config")
                    if not client_config:
                        st.error("Google Drive client configuration not found. Please add your OAuth2 credentials.")
                        return False
                    
                    flow = InstalledAppFlow.from_client_config(
                        client_config,
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                st.session_state.gdrive_credentials = creds
                st.session_state.gdrive_user_info = creds.id_token.get("email", "Google account")
            
            return True
        except Exception as e:
            st.error(f"Google Drive authentication failed: {e}")
            return False
    
    def sign_out(self):
        st.session_state.pop("gdrive_credentials", None)
        st.session_state.pop("gdrive_user_info", None)
    
    def get_user_info(self) -> Optional[str]:
        return st.session_state.get("gdrive_user_info")
    
    def backup(self, db: Database) -> Dict:
        """Backup database to Google Drive"""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        creds = st.session_state.get("gdrive_credentials")
        if not creds:
            raise RuntimeError("Not authenticated with Google Drive")
        
        service = build("drive", "v3", credentials=creds)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = os.path.join(temp_dir, self.BACKUP_FILE)
            db.create_backup_snapshot(snapshot_path)
            
            # Check if folder exists
            folder_query = f"name='{self.APP_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            folder_results = service.files().list(q=folder_query, fields="files(id)").execute()
            folders = folder_results.get("files", [])
            
            if folders:
                folder_id = folders[0]["id"]
            else:
                # Create folder
                folder_metadata = {
                    "name": self.APP_FOLDER,
                    "mimeType": "application/vnd.google-apps.folder"
                }
                folder = service.files().create(body=folder_metadata, fields="id").execute()
                folder_id = folder.get("id")
            
            # Check if file exists
            file_query = f"name='{self.BACKUP_FILE}' and '{folder_id}' in parents and trashed=false"
            file_results = service.files().list(q=file_query, fields="files(id)").execute()
            files = file_results.get("files", [])
            
            media = MediaFileUpload(snapshot_path, mimetype="application/x-sqlite3")
            
            if files:
                # Update existing file
                file_id = files[0]["id"]
                file = service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields="id,name,size,modifiedTime"
                ).execute()
            else:
                # Create new file
                file_metadata = {
                    "name": self.BACKUP_FILE,
                    "parents": [folder_id]
                }
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id,name,size,modifiedTime"
                ).execute()
        
        return {
            "name": file.get("name"),
            "size": file.get("size"),
            "modified": file.get("modifiedTime"),
        }
    
    def restore(self, db: Database):
        """Restore database from Google Drive"""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        creds = st.session_state.get("gdrive_credentials")
        if not creds:
            raise RuntimeError("Not authenticated with Google Drive")
        
        service = build("drive", "v3", credentials=creds)
        
        # Find the file
        folder_query = f"name='{self.APP_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folder_results = service.files().list(q=folder_query, fields="files(id)").execute()
        folders = folder_results.get("files", [])
        
        if not folders:
            raise RuntimeError(f"Backup folder '{self.APP_FOLDER}' not found")
        
        folder_id = folders[0]["id"]
        file_query = f"name='{self.BACKUP_FILE}' and '{folder_id}' in parents and trashed=false"
        file_results = service.files().list(q=file_query, fields="files(id)").execute()
        files = file_results.get("files", [])
        
        if not files:
            raise RuntimeError(f"Backup file '{self.BACKUP_FILE}' not found")
        
        file_id = files[0]["id"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = os.path.join(temp_dir, self.BACKUP_FILE)
            
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(download_path, "wb")
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            fh.close()
            db.replace_database_file(download_path)


class DropboxProvider(BackupProvider):
    """Dropbox backup provider"""
    
    APP_FOLDER = "/KUYAN"
    BACKUP_FILE = "kuyan.db"
    
    def get_name(self) -> str:
        return "Dropbox"
    
    def is_authenticated(self) -> bool:
        return st.session_state.get("dropbox_token") is not None
    
    def authenticate(self) -> bool:
        """Authenticate with Dropbox"""
        try:
            import dropbox
            from dropbox import DropboxOAuth2FlowNoRedirect
            
            app_key = st.session_state.get("dropbox_app_key")
            app_secret = st.session_state.get("dropbox_app_secret")
            
            if not app_key or not app_secret:
                st.error("Dropbox app credentials not configured. Please add your app key and secret.")
                return False
            
            auth_flow = DropboxOAuth2FlowNoRedirect(app_key, app_secret)
            authorize_url = auth_flow.start()
            
            st.info(f"1. Go to: {authorize_url}")
            st.info("2. Click 'Allow' (you might have to log in first)")
            st.info("3. Copy the authorization code and paste it below")
            
            auth_code = st.text_input("Enter the authorization code here:", key="dropbox_auth_code")
            
            if auth_code:
                try:
                    oauth_result = auth_flow.finish(auth_code)
                    st.session_state.dropbox_token = oauth_result.access_token
                    
                    # Get user info
                    dbx = dropbox.Dropbox(oauth_result.access_token)
                    account = dbx.users_get_current_account()
                    st.session_state.dropbox_user_info = account.email
                    
                    return True
                except Exception as e:
                    st.error(f"Failed to complete authentication: {e}")
                    return False
            
            return False
        except Exception as e:
            st.error(f"Dropbox authentication failed: {e}")
            return False
    
    def sign_out(self):
        st.session_state.pop("dropbox_token", None)
        st.session_state.pop("dropbox_user_info", None)
    
    def get_user_info(self) -> Optional[str]:
        return st.session_state.get("dropbox_user_info")
    
    def backup(self, db: Database) -> Dict:
        """Backup database to Dropbox"""
        import dropbox
        
        token = st.session_state.get("dropbox_token")
        if not token:
            raise RuntimeError("Not authenticated with Dropbox")
        
        dbx = dropbox.Dropbox(token)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = os.path.join(temp_dir, self.BACKUP_FILE)
            db.create_backup_snapshot(snapshot_path)
            
            with open(snapshot_path, "rb") as f:
                file_path = f"{self.APP_FOLDER}/{self.BACKUP_FILE}"
                metadata = dbx.files_upload(
                    f.read(),
                    file_path,
                    mode=dropbox.files.WriteMode.overwrite
                )
        
        return {
            "name": metadata.name,
            "size": metadata.size,
            "modified": metadata.server_modified.isoformat(),
        }
    
    def restore(self, db: Database):
        """Restore database from Dropbox"""
        import dropbox
        
        token = st.session_state.get("dropbox_token")
        if not token:
            raise RuntimeError("Not authenticated with Dropbox")
        
        dbx = dropbox.Dropbox(token)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = os.path.join(temp_dir, self.BACKUP_FILE)
            file_path = f"{self.APP_FOLDER}/{self.BACKUP_FILE}"
            
            metadata, response = dbx.files_download(file_path)
            
            with open(download_path, "wb") as f:
                f.write(response.content)
            
            db.replace_database_file(download_path)


class LocalFileProvider(BackupProvider):
    """Local file system backup provider"""
    
    BACKUP_FILE = "kuyan_backup.db"
    
    def get_name(self) -> str:
        return "Local File"
    
    def is_authenticated(self) -> bool:
        # Local file doesn't require authentication
        return True
    
    def authenticate(self) -> bool:
        # No authentication needed
        return True
    
    def sign_out(self):
        # No sign out needed
        pass
    
    def get_user_info(self) -> Optional[str]:
        return "Local System"
    
    def backup(self, db: Database) -> Dict:
        """Backup database to local file"""
        # Use Streamlit's file download
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = os.path.join(temp_dir, self.BACKUP_FILE)
            db.create_backup_snapshot(snapshot_path)
            
            with open(snapshot_path, "rb") as f:
                file_data = f.read()
            
            # Store in session state for download
            st.session_state.local_backup_data = file_data
            st.session_state.local_backup_filename = self.BACKUP_FILE
            
            file_size = len(file_data)
            
        return {
            "name": self.BACKUP_FILE,
            "size": file_size,
            "modified": datetime.now(timezone.utc).isoformat(),
        }
    
    def restore(self, db: Database):
        """Restore database from uploaded file"""
        uploaded_file = st.session_state.get("local_restore_file")
        if not uploaded_file:
            raise RuntimeError("No file uploaded for restore")

        uploaded_bytes = uploaded_file.getvalue()
        if not uploaded_bytes:
            raise RuntimeError("Uploaded file is empty")

        with tempfile.TemporaryDirectory() as temp_dir:
            uploaded_name = Path(getattr(uploaded_file, "name", self.BACKUP_FILE)).name or self.BACKUP_FILE
            restore_path = os.path.join(temp_dir, uploaded_name)

            with open(restore_path, "wb") as f:
                f.write(uploaded_bytes)

            try:
                with sqlite3.connect(restore_path) as conn:
                    conn.execute("PRAGMA schema_version;").fetchone()
            except sqlite3.DatabaseError as exc:
                raise RuntimeError("Uploaded file is not a valid SQLite database backup") from exc

            db.replace_database_file(restore_path)

