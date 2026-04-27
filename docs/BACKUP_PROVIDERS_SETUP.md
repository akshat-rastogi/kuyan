# KUYAN Backup Providers Setup Guide

This guide explains how to configure different cloud storage providers for backing up your KUYAN database.

## Overview

KUYAN now supports multiple backup providers:
- **OneDrive** - Microsoft's cloud storage
- **Google Drive** - Google's cloud storage
- **Dropbox** - Dropbox cloud storage
- **Local File** - Download/upload backup files directly (no cloud account needed)

## Local File Backup (Easiest - No Setup Required)

The Local File option requires no configuration:

1. Select "Local File" as your backup provider
2. Click "Backup to Local File" to download your database
3. Save the file to your preferred location (e.g., iCloud Drive folder, USB drive, etc.)
4. To restore, upload the backup file and click "Restore from Local File"

**Tip:** You can save the downloaded backup to your iCloud Drive folder manually:
- macOS: `~/Library/Mobile Documents/com~apple~CloudDocs/`
- This gives you iCloud backup without needing an API!

## OneDrive Setup

OneDrive works out of the box with a default public client ID.

### Using Default Configuration (Recommended)
1. Select "OneDrive" as your backup provider
2. Click "Sign In to OneDrive"
3. Follow the device code authentication flow
4. Your backups will be stored in `OneDrive/KUYAN/kuyan.db`

### Using Custom Azure App (Optional)
If you want to use your own Azure app registration:

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Set name (e.g., "KUYAN Backup")
5. Select "Accounts in any organizational directory and personal Microsoft accounts"
6. Set redirect URI to "Public client/native" with value `http://localhost`
7. After creation, copy the "Application (client) ID"
8. Go to "API permissions" → "Add a permission" → "Microsoft Graph"
9. Add delegated permissions: `Files.ReadWrite`, `User.Read`
10. In KUYAN, expand "OneDrive Configuration" and paste your Client ID

## Google Drive Setup

Google Drive requires OAuth 2.0 credentials.

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: KUYAN
   - User support email: your email
   - Developer contact: your email
   - Add scope: `../auth/drive.file`
4. Application type: "Desktop app"
5. Name: "KUYAN Desktop"
6. Click "Create"
7. Download the JSON file

### Step 3: Configure in KUYAN
1. Select "Google Drive" as your backup provider
2. Expand "Google Drive Configuration"
3. Open the downloaded JSON file in a text editor
4. Copy the entire JSON content
5. Paste it into the "OAuth 2.0 Client Configuration" text area
6. Click "Sign In to Google Drive"
7. Complete the OAuth flow in your browser

Your backups will be stored in `Google Drive/KUYAN/kuyan.db`

## Dropbox Setup

Dropbox requires creating an app in the Dropbox App Console.

### Step 1: Create Dropbox App
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose "Scoped access"
4. Choose "App folder" (recommended) or "Full Dropbox"
5. Name your app (e.g., "KUYAN Backup")
6. Click "Create app"

### Step 2: Configure Permissions
1. Go to the "Permissions" tab
2. Enable the following permissions:
   - `files.metadata.write`
   - `files.metadata.read`
   - `files.content.write`
   - `files.content.read`
3. Click "Submit"

### Step 3: Get App Credentials
1. Go to the "Settings" tab
2. Copy the "App key"
3. Copy the "App secret"

### Step 4: Configure in KUYAN
1. Select "Dropbox" as your backup provider
2. Expand "Dropbox Configuration"
3. Paste your App key
4. Paste your App secret
5. Click "Sign In to Dropbox"
6. Follow the authorization flow:
   - Copy the URL and open it in your browser
   - Click "Allow"
   - Copy the authorization code
   - Paste it back in KUYAN

Your backups will be stored in `Dropbox/Apps/KUYAN/kuyan.db` (if using App folder access)

## Security Considerations

### Credentials Storage
- All credentials are stored in Streamlit's session state (memory only)
- Credentials are cleared when you close the browser or sign out
- For Google Drive and Dropbox, you need to re-authenticate each session

### Access Tokens
- OneDrive: Tokens are refreshed automatically when expired
- Google Drive: Tokens are refreshed automatically when expired
- Dropbox: You need to re-authenticate each session

### Best Practices
1. **Use App-specific passwords** when available
2. **Don't share your credentials** with others
3. **Regularly backup** your database to multiple locations
4. **Test restore** periodically to ensure backups work
5. **Keep credentials secure** - don't commit them to version control

## Troubleshooting

### OneDrive Issues
- **"Session expired"**: Click "Sign In" again
- **"Upload failed"**: Check your internet connection and OneDrive storage space
- **"File not found"**: Ensure you've created at least one backup first

### Google Drive Issues
- **"Invalid JSON"**: Ensure you copied the entire OAuth client JSON correctly
- **"Authentication failed"**: Make sure the Google Drive API is enabled in your project
- **"Permission denied"**: Check that you've added the correct scopes in the OAuth consent screen

### Dropbox Issues
- **"App credentials not configured"**: Enter both App key and App secret
- **"Authorization failed"**: Make sure you copied the authorization code correctly
- **"File not found"**: Ensure you've created at least one backup first

### General Issues
- **"Backup failed"**: Check your internet connection and provider storage space
- **"Restore failed"**: Ensure the backup file exists and is not corrupted
- **"Provider not responding"**: Try signing out and signing in again

## Switching Between Providers

You can use multiple providers and switch between them:

1. Each provider stores backups independently
2. Backups from one provider cannot be directly restored by another
3. You can backup to multiple providers for redundancy
4. Use Local File to manually transfer backups between providers

## Backup File Format

All providers store the same SQLite database file (`kuyan.db`):
- Format: SQLite 3 database
- Contains: All your accounts, snapshots, settings, and data
- Size: Typically 100KB - 10MB depending on data volume

## Recommended Backup Strategy

For maximum data safety:

1. **Primary**: Use a cloud provider (OneDrive, Google Drive, or Dropbox) for automatic backups
2. **Secondary**: Periodically download Local File backups to external storage
3. **Frequency**: Backup after significant data changes or at least monthly
4. **Testing**: Test restore functionality quarterly to ensure backups work

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the provider's documentation
- Open an issue on the KUYAN GitHub repository

---

Made with Bob