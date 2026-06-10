from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.db.database import get_db

from app.models.user import User

from app.schemas.project import (
    ProjectCreate,
    ProjectResponse
)

from app.api.deps import get_current_user

from app.services import projectService

from app.core.exceptions import (
    ProjectNotFoundException
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

######################Create Project
@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await projectService.create_project(
        db=db,
        name=payload.name,
        current_user=current_user
    )
######################


######################Get User Projects
@router.get(
    "",
    response_model=list[ProjectResponse]
)
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return projectService.get_user_projects(
        db=db,
        current_user=current_user
    )
######################

######################Open Project
@router.post(
    "/{project_id}/open",
    response_model=ProjectResponse
)
async def open_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        return await projectService.open_project(
            db=db,
            project_id=project_id,
            current_user=current_user
        )

    except ProjectNotFoundException as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
######################

######################Close Project
@router.post(
    "/{project_id}/close",
    response_model=ProjectResponse
)
async def close_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        return await projectService.close_project(
            db=db,
            project_id=project_id,
            current_user=current_user
        )

    except ProjectNotFoundException as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
######################

######################Delete Project
@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        await projectService.delete_project(
            db=db,
            project_id=project_id,
            current_user=current_user
        )

    except ProjectNotFoundException as e:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
######################
