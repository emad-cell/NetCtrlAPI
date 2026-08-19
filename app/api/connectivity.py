from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.exceptions import (
    ConnectivityResultParseException,
    DeviceTypeUndeterminedException,
    NetmikoAuthException,
    NetmikoUnreachableException,
    ProjectNotFoundException,
    UnsupportedAutomationException,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.connectivity import (
    ConnectivityCheckResponse,
    ConnectivityEndpointsResponse,
    PingRequest,
    PingResponse,
)
from app.services import connectivityService


router = APIRouter(
    prefix="/projects/{project_id}/nodes/{node_id}/connectivity",
    tags=["Connectivity"],
)

endpoints_router = APIRouter(
    prefix="/projects/{project_id}/connectivity",
    tags=["Connectivity"],
)


@endpoints_router.get(
    "/endpoints",
    response_model=ConnectivityEndpointsResponse,
)
async def list_connectivity_endpoints(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await connectivityService.discover_project_interfaces(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@endpoints_router.post(
    "/check",
    response_model=ConnectivityCheckResponse,
)
async def check_project_connectivity(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await connectivityService.check_project_connectivity(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )



@router.post(
    "/ping",
    response_model=PingResponse,
)
async def ping_node(
    project_id: int,
    node_id: str,
    payload: PingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await connectivityService.run_node_ping(
            db=db,
            project_id=project_id,
            node_id=node_id,
            destination=payload.destination,
            current_user=current_user,
        )
    except ProjectNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except NetmikoAuthException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    except NetmikoUnreachableException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except (
        DeviceTypeUndeterminedException,
        UnsupportedAutomationException,
        ConnectivityResultParseException,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
