from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundException, GNS3RequestException
from app.db.database import get_db
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse
from app.services import linkService

router = APIRouter(
    prefix="/projects/{project_id}/links",
    tags=["Links"],
)


########################## List Links ##########################
@router.get(
    "",
    response_model=list[LinkResponse],
)
async def list_links(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await linkService.get_links(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except GNS3RequestException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
################################################################

########################## Get Link ###########################
@router.get(
    "/{link_id}",
    response_model=LinkResponse,
)
async def get_link(
    project_id: int,
    link_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await linkService.get_link(
            db=db,
            project_id=project_id,
            link_id=link_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except GNS3RequestException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
################################################################

########################## Create Link ########################
@router.post(
    "",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_link(
    project_id: int,
    payload: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await linkService.create_link(
            db=db,
            project_id=project_id,
            payload=payload,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except GNS3RequestException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
################################################################

########################## Delete Link ########################
@router.delete(
    "/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_link(
    project_id: int,
    link_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await linkService.delete_link(
            db=db,
            project_id=project_id,
            link_id=link_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except GNS3RequestException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
################################################################