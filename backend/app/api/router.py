from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def api_status():
    return {"status": "API is running", "version": "0.1.0"}