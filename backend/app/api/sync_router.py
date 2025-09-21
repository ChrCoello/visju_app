from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.services.file_sync_service import FileSyncService
from app.core.logging import get_logger

logger = get_logger()
router = APIRouter(prefix="/sync", tags=["synchronization"])

@router.get("/status")
async def get_sync_status() -> Dict[str, Any]:
    """Get current file synchronization status."""
    try:
        sync_service = FileSyncService()

        if not sync_service.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize sync service")

        status = sync_service.sync_status()

        if not status:
            raise HTTPException(status_code=500, detail="Failed to get sync status")

        return {
            "status": "success",
            "data": status
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download-missing")
async def download_missing_files(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Download files that are missing locally from Google Drive."""
    try:
        sync_service = FileSyncService()

        if not sync_service.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize sync service")

        # Get current status to check what needs downloading
        status = sync_service.sync_status()
        comparison = status.get('sync_comparison', {})

        missing_count = len(comparison.get('missing_locally', []))
        mismatch_count = len(comparison.get('size_mismatches', []))

        if missing_count == 0 and mismatch_count == 0:
            return {
                "status": "success",
                "message": "No files need to be downloaded",
                "files_to_download": 0
            }

        # Start download in background
        def download_task():
            try:
                logger.info("Starting background download task")
                sync_service.download_missing_files()
                logger.info("Background download task completed")
            except Exception as e:
                logger.error(f"Error in background download task: {e}")

        background_tasks.add_task(download_task)

        return {
            "status": "success",
            "message": "Download started in background",
            "files_to_download": missing_count + mismatch_count
        }

    except Exception as e:
        logger.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/full-sync")
async def perform_full_sync() -> Dict[str, Any]:
    """Perform a complete synchronization of Drive files to local storage."""
    try:
        sync_service = FileSyncService()
        result = sync_service.full_sync()

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Full sync failed')
            )

        return {
            "status": "success",
            "message": "Full synchronization completed",
            "data": result
        }

    except Exception as e:
        logger.error(f"Error during full sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-stats")
async def get_storage_stats() -> Dict[str, Any]:
    """Get local storage statistics."""
    try:
        from app.services.file_storage_service import FileStorageService

        storage_service = FileStorageService()
        stats = storage_service.get_storage_stats()

        return {
            "status": "success",
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))