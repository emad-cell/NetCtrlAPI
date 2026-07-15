from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundException
from app.db.database import get_db
from app.models.user import User
from app.schemas.topology import TopologyResponse
from app.services import topologyService
from fastapi.responses import Response
router = APIRouter(
    prefix="/projects/{project_id}/topology",
    tags=["Topology"],
)


########################## Get Topology ##########################
@router.get(
    "",
    response_model=TopologyResponse,
)
async def get_topology(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await topologyService.get_topology(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
####################################################################
########################## Export Topology Image ##################
@router.get(
    "/export",
)
async def export_topology(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        image_bytes = await topologyService.get_topology_image(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return Response(
        content=image_bytes,
        media_type="image/png",
    )
####################################################################