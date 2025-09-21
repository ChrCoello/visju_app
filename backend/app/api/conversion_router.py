from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from app.services.audio_conversion_service import AudioConversionService
from app.core.logging import get_logger

logger = get_logger()
router = APIRouter(prefix="/conversion", tags=["audio conversion"])

@router.get("/status")
async def get_conversion_status() -> Dict[str, Any]:
    """Get current audio conversion status and statistics."""
    try:
        conversion_service = AudioConversionService()
        stats = conversion_service.get_conversion_stats()

        return {
            "status": "success",
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting conversion status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dependencies")
async def check_dependencies() -> Dict[str, Any]:
    """Check if required dependencies (Pydub, Mutagen, FFmpeg) are available."""
    try:
        conversion_service = AudioConversionService()
        deps = conversion_service.check_dependencies()

        missing_deps = [name for name, available in deps.items() if not available]

        return {
            "status": "success",
            "dependencies": deps,
            "all_available": len(missing_deps) == 0,
            "missing": missing_deps
        }

    except Exception as e:
        logger.error(f"Error checking dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert/{filename}")
async def convert_single_file(filename: str) -> Dict[str, Any]:
    """Convert a single audio file from M4A to WAV."""
    try:
        conversion_service = AudioConversionService()

        # Get the input file path
        input_path = conversion_service.storage_service.get_original_file_path(filename)

        if not input_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename}"
            )

        # Perform conversion
        result = conversion_service.convert_m4a_to_wav(str(input_path))

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Conversion failed: {result.error_message}"
            )

        return {
            "status": "success",
            "message": f"Successfully converted {filename}",
            "data": {
                "original_path": result.original_path,
                "converted_path": result.converted_path,
                "conversion_duration_ms": result.conversion_duration_ms
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert-all")
async def convert_all_files(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Convert all audio files in the originals directory."""
    try:
        conversion_service = AudioConversionService()

        # Check if there are files to convert
        stats = conversion_service.get_conversion_stats()
        if stats['original_files'] == 0:
            return {
                "status": "success",
                "message": "No audio files found to convert",
                "files_to_convert": 0
            }

        # Start conversion in background
        def conversion_task():
            try:
                logger.info("Starting background conversion task")
                results = conversion_service.batch_convert_files()
                successful = sum(1 for r in results.values() if r.success)
                logger.info(f"Background conversion completed: {successful}/{len(results)} successful")
            except Exception as e:
                logger.error(f"Error in background conversion task: {e}")

        background_tasks.add_task(conversion_task)

        return {
            "status": "success",
            "message": "Batch conversion started in background",
            "files_to_convert": stats['original_files']
        }

    except Exception as e:
        logger.error(f"Error starting batch conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{filename}")
async def get_file_metadata(filename: str) -> Dict[str, Any]:
    """Get metadata for an audio file."""
    try:
        conversion_service = AudioConversionService()

        # Try original file first, then converted
        input_path = conversion_service.storage_service.get_original_file_path(filename)

        if not input_path.exists():
            # Try converted file
            converted_path = conversion_service.storage_service.get_converted_file_path(filename)
            if converted_path.exists():
                input_path = converted_path
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {filename}"
                )

        metadata = conversion_service.extract_metadata(str(input_path))

        if metadata is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract metadata"
            )

        return {
            "status": "success",
            "data": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metadata for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))