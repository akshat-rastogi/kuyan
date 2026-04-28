"""
KUYAN - Monthly Net Worth Tracker
Backup & Restore Settings Module - Multi-provider backup and restore functionality
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st

from database import Database
from backup_providers import (
    OneDriveProvider,
    GoogleDriveProvider,
    DropboxProvider,
    LocalFileProvider,
)


def backup_restore_settings(db: Database, key_prefix: str = ""):
    """
    Render the Backup & Restore settings page with multiple provider support.

    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """
    if "sandbox" in db.db_path:
        st.info("Cloud backup and restore is disabled in sandbox mode.")
        return

    st.caption("Back up your KUYAN database to cloud storage or local file, or restore from backup.")

    # Provider selection
    providers = {
        "OneDrive": OneDriveProvider(),
        "Google Drive": GoogleDriveProvider(),
        "Dropbox": DropboxProvider(),
        "Local File": LocalFileProvider(),
    }

    # Initialize selected provider in session state
    if "backup_provider" not in st.session_state:
        st.session_state.backup_provider = "Local File"

    selected_provider_name = st.selectbox(
        "Select Backup Provider",
        options=list(providers.keys()),
        index=list(providers.keys()).index(st.session_state.backup_provider),
        key=f"{key_prefix}provider_select",
        help="Choose where to store your backups",
    )
    st.session_state.backup_provider = selected_provider_name

    provider = providers[selected_provider_name]

    st.divider()

    # Provider-specific configuration
    if selected_provider_name == "OneDrive":
        render_onedrive_config(key_prefix)
    elif selected_provider_name == "Google Drive":
        render_google_drive_config(key_prefix)
    elif selected_provider_name == "Dropbox":
        render_dropbox_config(key_prefix)

    # Authentication status
    if provider.is_authenticated():
        user_info = provider.get_user_info()
        st.success(f"✓ Signed in to {provider.get_name()}" + (f" as {user_info}" if user_info and user_info != "Local System" else ""))
    else:
        if selected_provider_name != "Local File":
            st.warning(f"Not signed in to {provider.get_name()}")

    # Authentication buttons (not needed for Local File)
    if selected_provider_name != "Local File":
        col_auth_1, col_auth_2 = st.columns(2)

        with col_auth_1:
            if st.button(
                f"🔐 Sign In to {provider.get_name()}",
                key=f"{key_prefix}signin_{selected_provider_name}",
                type="primary",
                use_container_width=True,
            ):
                if provider.authenticate():
                    st.success(f"Successfully signed in to {provider.get_name()}")
                    st.rerun()

        with col_auth_2:
            if provider.is_authenticated():
                if st.button(
                    "🚪 Sign Out",
                    key=f"{key_prefix}signout_{selected_provider_name}",
                    use_container_width=True,
                ):
                    provider.sign_out()
                    st.success(f"Signed out from {provider.get_name()}")
                    st.rerun()

        st.divider()

    # Backup and Restore operations
    if provider.is_authenticated() or selected_provider_name == "Local File":
        col_backup, col_restore = st.columns(2)

        with col_backup:
            st.markdown("#### Backup Database")
            if selected_provider_name == "Local File":
                st.write("Download your database file to your computer.")
            else:
                st.write(f"Upload your database to {provider.get_name()}.")

            if st.button(
                f"☁️ Backup to {provider.get_name()}",
                key=f"{key_prefix}backup_btn",
                use_container_width=True,
                type="primary",
            ):
                try:
                    metadata = provider.backup(db)
                    
                    if selected_provider_name == "Local File":
                        # Provide download button
                        backup_data = st.session_state.get("local_backup_data")
                        backup_filename = st.session_state.get("local_backup_filename", "kuyan_backup.db")
                        
                        if backup_data:
                            st.download_button(
                                label="📥 Download Backup File",
                                data=backup_data,
                                file_name=backup_filename,
                                mime="application/x-sqlite3",
                                key=f"{key_prefix}download_backup",
                                use_container_width=True,
                            )
                            st.success("Backup ready for download!")
                    else:
                        st.session_state[f"last_{selected_provider_name}_backup"] = metadata
                        st.success(f"Database backed up to {provider.get_name()} successfully!")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Backup failed: {exc}")

        with col_restore:
            st.markdown("#### Restore Database")
            if selected_provider_name == "Local File":
                st.write("Upload a database file from your computer.")
                
                uploaded_file = st.file_uploader(
                    "Choose backup file",
                    type=["db", "sqlite", "sqlite3"],
                    key=f"{key_prefix}file_upload",
                    help="Select a KUYAN backup database file (.db, .sqlite, or .sqlite3). iOS may rename database files during upload.",
                )
                
                if uploaded_file:
                    st.session_state.local_restore_file = uploaded_file
            else:
                st.write(f"Download and restore from {provider.get_name()}.")

            confirm_restore = st.checkbox(
                "I understand this will overwrite my current database",
                key=f"{key_prefix}confirm_restore",
            )

            restore_enabled = confirm_restore and (
                selected_provider_name != "Local File" or st.session_state.get("local_restore_file")
            )

            if st.button(
                f"⬇️ Restore from {provider.get_name()}",
                key=f"{key_prefix}restore_btn",
                use_container_width=True,
                disabled=not restore_enabled,
            ):
                if not confirm_restore:
                    st.error("Please confirm overwrite before restoring.")
                else:
                    try:
                        provider.restore(db)
                        st.session_state.clear_cache = True
                        st.session_state.restore_completed = True
                        st.success("Database restored successfully! Reloading app...")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Restore failed: {exc}")
    else:
        st.info(f"Please sign in to {provider.get_name()} to access backup and restore features.")

    # Show last backup metadata (not for Local File)
    if selected_provider_name != "Local File":
        render_backup_metadata(selected_provider_name)


def render_onedrive_config(key_prefix: str):
    """Render OneDrive-specific configuration"""
    with st.expander("⚙️ OneDrive Configuration", expanded=False):
        default_client_id = "04f0c124-f2bc-4f59-8241-bf6df9866bbd"
        client_id = st.text_input(
            "Microsoft App Client ID",
            value=st.session_state.get("onedrive_client_id", default_client_id),
            key=f"{key_prefix}onedrive_client_id",
            help="You can use the default public client ID or replace it with your own Azure app registration client ID.",
        )
        st.session_state.onedrive_client_id = client_id.strip() or default_client_id


def render_google_drive_config(key_prefix: str):
    """Render Google Drive-specific configuration"""
    with st.expander("⚙️ Google Drive Configuration", expanded=False):
        st.markdown("""
        **Setup Instructions:**
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select existing one
        3. Enable Google Drive API
        4. Create OAuth 2.0 credentials (Desktop app)
        5. Download the JSON and paste the content below
        """)
        
        client_config_json = st.text_area(
            "OAuth 2.0 Client Configuration (JSON)",
            value=st.session_state.get("gdrive_client_config_json", ""),
            key=f"{key_prefix}gdrive_config",
            height=150,
            help="Paste your OAuth 2.0 client configuration JSON here",
        )
        
        if client_config_json:
            import json
            try:
                config = json.loads(client_config_json)
                st.session_state.gdrive_client_config = config
                st.session_state.gdrive_client_config_json = client_config_json
                st.success("✓ Configuration loaded")
            except json.JSONDecodeError:
                st.error("Invalid JSON format")


def render_dropbox_config(key_prefix: str):
    """Render Dropbox-specific configuration"""
    with st.expander("⚙️ Dropbox Configuration", expanded=False):
        st.markdown("""
        **Setup Instructions:**
        1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
        2. Create a new app with "Scoped access" and "App folder" access
        3. Copy your App key and App secret below
        """)
        
        app_key = st.text_input(
            "Dropbox App Key",
            value=st.session_state.get("dropbox_app_key", ""),
            key=f"{key_prefix}dropbox_key",
            type="password",
        )
        
        app_secret = st.text_input(
            "Dropbox App Secret",
            value=st.session_state.get("dropbox_app_secret", ""),
            key=f"{key_prefix}dropbox_secret",
            type="password",
        )
        
        if app_key:
            st.session_state.dropbox_app_key = app_key
        if app_secret:
            st.session_state.dropbox_app_secret = app_secret
        
        if app_key and app_secret:
            st.success("✓ Credentials configured")


def render_backup_metadata(provider_name: str):
    """Render the last successful backup metadata if available."""
    backup_info = st.session_state.get(f"last_{provider_name}_backup")
    if not backup_info:
        return

    st.divider()
    st.markdown(f"#### Last {provider_name} Backup")
    st.write(f"**File:** {backup_info.get('name', 'kuyan.db')}")
    size_bytes = backup_info.get("size")
    if size_bytes is not None:
        st.write(f"**Size:** {format_bytes(int(size_bytes))}")
    if backup_info.get("modified"):
        st.write(f"**Modified:** {backup_info['modified']}")


def format_bytes(size_bytes: int) -> str:
    """Format byte count for display."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"

