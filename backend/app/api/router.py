from fastapi import APIRouter
from .sync_router import router as sync_router
from .conversion_router import router as conversion_router

router = APIRouter()

# Include sub-routers
router.include_router(sync_router)
router.include_router(conversion_router)

@router.get("/status")
async def api_status():
    return {"status": "API is running", "version": "0.1.0"}