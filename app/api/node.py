from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundException
from app.db.database import get_db
from app.models.user import User
from app.schemas.node import (
    NodeCreate,
    NodeResponse,
    NodeUpdate,
    NodeUpdatePosition,
)
from app.services import nodeService

router = APIRouter(
    prefix="/projects/{project_id}/nodes",
    tags=["Nodes"],
)

########################## List Nodes ##########################

@router.get(
    "",
    response_model=list[NodeResponse],
)
async def list_nodes(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await nodeService.get_nodes(
            db=db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

########################## Get Node ##########################

@router.get(
    "/{node_id}",
    response_model=NodeResponse,
)
async def get_node(
    project_id: int,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await nodeService.get_node(
            db=db,
            project_id=project_id,
            node_id=node_id,
            current_user=current_user,
        )
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

########################## Create Node ##########################

@router.post(
    "",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_node(
    project_id: int,
    payload: NodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await nodeService.create_node(
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

########################## Start Node ##########################

@router.post(
    "/{node_id}/start",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def start_node(
    project_id: int,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await nodeService.start_node(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

########################## Stop Node ##########################

@router.post(
    "/{node_id}/stop",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def stop_node(
    project_id: int,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await nodeService.stop_node(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

########################## Reload Node ##########################

@router.post(
    "/{node_id}/reload",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reload_node(
    project_id: int,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await nodeService.reload_node(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

########################## Delete Node ##########################

@router.delete(
    "/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_node(
    project_id: int,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await nodeService.delete_node(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

########################## Rename Node ##########################

@router.patch(
    "/{node_id}",
    response_model=NodeResponse,
)
async def rename_node(
    project_id: int,
    node_id: str,
    payload: NodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await nodeService.rename_node(
        db=db,
        project_id=project_id,
        node_id=node_id,
        payload=payload,
        current_user=current_user,
    )

########################## Move Node ##########################

@router.patch(
    "/{node_id}/position",
    response_model=NodeResponse,
)
async def move_node(
    project_id: int,
    node_id: str,
    payload: NodeUpdatePosition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await nodeService.move_node(
        db=db,
        project_id=project_id,
        node_id=node_id,
        payload=payload,
        current_user=current_user,
    )