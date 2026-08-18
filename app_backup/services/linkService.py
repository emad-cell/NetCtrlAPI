from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.link import LinkCreate
from app.services.projectService import get_project_by_id
from app.services.Gns3.Link import (
    get_links as get_gns3_links,
    get_link as get_gns3_link,
    create_link as create_gns3_link,
    delete_link as delete_gns3_link,
)


########################## List Links ##########################
async def get_links(
    db: Session,
    project_id: int,
    current_user: User,
) -> list:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    return await get_gns3_links(
        project_id=str(project.project_id),
    )
################################################################

########################## Get Link ###########################
async def get_link(
    db: Session,
    project_id: int,
    link_id: str,
    current_user: User,
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    return await get_gns3_link(
        project_id=str(project.project_id),
        link_id=link_id,
    )
################################################################

########################## Create Link ########################
async def create_link(
    db: Session,
    project_id: int,
    payload: LinkCreate,
    current_user: User,
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    gns3_payload = {
        "nodes": [
            {
                "node_id": payload.source.node_id,
                "adapter_number": payload.source.adapter,
                "port_number": payload.source.port,
            },
            {
                "node_id": payload.target.node_id,
                "adapter_number": payload.target.adapter,
                "port_number": payload.target.port,
            },
        ]
    }

    return await create_gns3_link(
        project_id=str(project.project_id),
        payload=gns3_payload,
    )
################################################################

########################## Delete Link ########################
async def delete_link(
    db: Session,
    project_id: int,
    link_id: str,
    current_user: User,
) -> None:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    await delete_gns3_link(
        project_id=str(project.project_id),
        link_id=link_id,
    )
################################################################