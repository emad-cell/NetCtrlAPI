from sqlalchemy.orm import Session

from app.models.user import User
from app.services.projectService import get_project_by_id
from app.services.Gns3.Nodes import get_nodes as get_gns3_nodes
from app.services.Gns3.Link import get_links as get_gns3_links
from app.services.topologyRender import render_topology_image


########################## Get Topology ##########################
async def get_topology(
    db: Session,
    project_id: int,
    current_user: User,
) -> dict:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    nodes = await get_gns3_nodes(
        project_id=str(project.project_id),
    )

    links = await get_gns3_links(
        project_id=str(project.project_id),
    )

    return {
        "project": project,
        "nodes": nodes,
        "links": links,
    }
####################################################################

########################## Export Topology Image ##################
async def get_topology_image(
    db: Session,
    project_id: int,
    current_user: User,
) -> bytes:

    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    nodes = await get_gns3_nodes(
        project_id=str(project.project_id),
    )

    links = await get_gns3_links(
        project_id=str(project.project_id),
    )

    return render_topology_image(
        nodes=nodes,
        links=links,
    )
####################################################################