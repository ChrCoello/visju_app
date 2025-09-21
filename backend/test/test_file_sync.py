#!/usr/bin/env python3
"""
Test script for file synchronization between Google Drive and local storage.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.file_sync_service import FileSyncService
from app.services.file_storage_service import FileStorageService
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🔄 Testing File Synchronization System")
    print("=" * 50)

    # Test 1: Initialize services
    print("\n1. 🚀 Initializing services...")
    sync_service = FileSyncService()
    storage_service = FileStorageService()

    if not sync_service.initialize():
        print("❌ Failed to initialize sync service")
        return False

    print("✅ Services initialized successfully")

    # Test 2: Set up storage structure
    print("\n2. 📁 Setting up storage structure...")
    if storage_service.setup_storage_structure():
        print("✅ Storage structure created")

        # Show storage paths
        paths = storage_service.get_storage_paths()
        for name, path in paths.items():
            print(f"   📂 {name}: {path}")
    else:
        print("❌ Failed to set up storage structure")
        return False

    # Test 3: Check current sync status
    print("\n3. 📊 Checking current sync status...")
    status = sync_service.sync_status()

    if status:
        comparison = status.get('sync_comparison', {})
        print(f"✅ Sync status retrieved")
        print(f"   📥 Files missing locally: {len(comparison.get('missing_locally', []))}")
        print(f"   📤 Files missing on Drive: {len(comparison.get('missing_on_drive', []))}")
        print(f"   ✨ Files in both locations: {len(comparison.get('present_both', []))}")
        print(f"   ⚠️  Size mismatches: {len(comparison.get('size_mismatches', []))}")

        # Show missing files
        missing = comparison.get('missing_locally', [])
        if missing:
            print(f"\n   📝 Files missing locally:")
            for file_key in missing[:5]:  # Show first 5
                print(f"      - {file_key}")
            if len(missing) > 5:
                print(f"      ... and {len(missing) - 5} more")

    else:
        print("❌ Failed to get sync status")
        return False

    # Test 4: Get storage statistics
    print("\n4. 📈 Storage statistics...")
    stats = storage_service.get_storage_stats()
    for category, data in stats.items():
        print(f"   📊 {category}: {data['file_count']} files, {data['total_size_mb']:.2f} MB")

    # Test 5: Ask user if they want to perform sync
    print("\n5. 🔄 File synchronization...")
    if status.get('is_synced', False):
        print("✅ All files are already synchronized!")
    else:
        missing_count = len(comparison.get('missing_locally', []))
        mismatch_count = len(comparison.get('size_mismatches', []))

        if missing_count > 0 or mismatch_count > 0:
            print(f"📥 {missing_count} files need to be downloaded")
            print(f"🔄 {mismatch_count} files have size mismatches")

            response = input("\nDo you want to download missing files? (y/N): ")
            if response.lower() == 'y':
                print("\n📥 Starting file download...")
                download_results = sync_service.download_missing_files()

                successful = sum(1 for result in download_results.values() if result)
                total = len(download_results)

                print(f"✅ Download completed: {successful}/{total} files successful")

                # Check final status
                final_status = sync_service.sync_status()
                if final_status.get('is_synced', False):
                    print("🎉 All files are now synchronized!")
                else:
                    print("⚠️  Some files may still need attention")
            else:
                print("⏭️  Skipping download")

    # Test 6: Show final summary
    print("\n6. 📋 Final Summary...")
    final_stats = storage_service.get_storage_stats()
    originals = final_stats.get('originals', {})
    print(f"   📂 Local original files: {originals.get('file_count', 0)}")
    print(f"   💾 Total storage used: {originals.get('total_size_mb', 0):.2f} MB")

    print("\n🎉 File synchronization test completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)