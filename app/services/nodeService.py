from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.projectService import get_project_by_id
from app.schemas.node import NodeCreate , NodeUpdatePosition, NodeUpdate
from app.services.Gns3.Nodes import (
    create_node as create_gns3_node,
    start_node as start_gns3_node,
    stop_node as stop_gns3_node,
    reload_node as reload_gns3_node,
    delete_node as delete_gns3_node,
    rename_node as rename_gns3_node,
    move_node as move_gns3_node,
    get_nodes as get_gns3_nodes,
    get_node as get_gns3_node,


)


##########################List Nodes
async def get_nodes(
    db: Session,
    project_id: int,
    current_user: User
) -> list:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user
    )

    return await get_gns3_nodes(
        project_id=str(project.project_id)
    )
##########################

##########################Get Node
async def get_node(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user
    )

    return await get_gns3_node(
        project_id=str(project.project_id),
        node_id=node_id
    )
##########################

##########################Create Node from Template
async def create_node(
    db: Session,
    project_id: int,
    payload: NodeCreate,
    current_user: User,
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    node = await create_gns3_node(
        project.project_id,
        payload.model_dump(exclude_none=True),
    )

    return node
##########################
##########################Start Node
async def start_node(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
) -> None:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    await start_gns3_node(
        str(project.project_id),
        node_id,
    )
##########################

##########################Stop Node
async def stop_node(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
) -> None:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    await stop_gns3_node(
        str(project.project_id),
        node_id,
    )
##########################

##########################Reload
async def reload_node(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
) -> None:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    await reload_gns3_node(
        str(project.project_id),
        node_id,
    )
##########################

##########################Delete
async def delete_node(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
) -> None:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    await delete_gns3_node(
        str(project.project_id),
        node_id,
    )
##########################

##########################Rename
async def rename_node(
    db: Session,
    project_id: int,
    node_id: str,
    payload: NodeUpdate,
    current_user: User,
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    return await rename_gns3_node(
        str(project.project_id),
        node_id,
        payload.name,
    )
##########################

##########################Move
async def move_node(
    db: Session,
    project_id: int,
    node_id: str,
    payload: NodeUpdatePosition,
    current_user: User,
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    return await move_gns3_node(
        str(project.project_id),
        node_id,
        payload.x,
        payload.y,
    )
###########################