#!/usr/bin/env python3
"""
Simple test script for Google Drive authentication and folder access.
Run this to verify your Google Drive setup is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.google_drive_service import GoogleDriveService
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🔍 Testing Google Drive Authentication")
    print("=" * 50)

    # Print configuration
    print(f"📁 Credentials path: {settings.GOOGLE_DRIVE_CREDENTIALS_PATH}")
    print(f"📂 Folder ID: {settings.GOOGLE_DRIVE_FOLDER_ID}")
    print()

    # Check if credentials file exists
    if not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH):
        print(f"❌ Credentials file not found: {settings.GOOGLE_DRIVE_CREDENTIALS_PATH}")
        print("   Please ensure your service account JSON file is in the correct location.")
        return False

    if not settings.GOOGLE_DRIVE_FOLDER_ID:
        print("❌ GOOGLE_DRIVE_FOLDER_ID not set in environment variables")
        print("   Please set this in your .env file")
        return False

    # Create service instance
    drive_service = GoogleDriveService()

    # Test authentication
    print("🔐 Testing authentication...")
    auth_success = drive_service.authenticate()

    if not auth_success:
        print("❌ Authentication failed")
        return False

    print("✅ Authentication successful")

    # Test connection
    print("\n🌐 Testing connection...")
    connection_result = drive_service.test_connection()

    if not connection_result["success"]:
        print(f"❌ Connection failed: {connection_result['error']}")
        return False

    print(f"✅ Connected as: {connection_result['user_email']}")

    # Test folder access
    print(f"\n📂 Testing folder access...")
    folder_result = drive_service.test_folder_access()

    if not folder_result["success"]:
        print(f"❌ Folder access failed: {folder_result['error']}")
        print(f"   Folder ID: {folder_result.get('folder_id', 'Unknown')}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure the folder is shared with your service account email")
        print("   2. Check that the folder ID is correct")
        print("   3. Verify the service account has read permissions")
        return False

    print(f"✅ Folder access successful")
    print(f"   Folder name: {folder_result['folder_name']}")
    print(f"   Files found: {folder_result['file_count']}")

    if folder_result['sample_files']:
        print("   Sample files:")
        for file_info in folder_result['sample_files']:
            print(f"     - {file_info['name']} ({file_info['mimeType']})")

    print("\n🎉 All tests passed! Google Drive integration is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)