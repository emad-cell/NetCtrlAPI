from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.services.Gns3.server import (
    start_gns3_server,
    stop_gns3_server,
    get_server_status,
)

router = APIRouter(prefix="/server", tags=["Server"])


@router.post(
    "/start",
    status_code=status.HTTP_200_OK,
)
async def start_server(
    current_user: User = Depends(get_current_user)  # ✅ محمي
):
    try:
        await start_gns3_server()
        return {"message": "GNS3 server started", **get_server_status()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start GNS3 server: {str(e)}"
        )


@router.post(
    "/stop",
    status_code=status.HTTP_200_OK,
)
async def stop_server(
    current_user: User = Depends(get_current_user)  # ✅ محمي
):
    try:
        await stop_gns3_server()
        return {"message": "GNS3 server stopped", **get_server_status()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop GNS3 server: {str(e)}"
        )


@router.get("/status")
async def server_status():
    return get_server_status()