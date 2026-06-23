from sqlalchemy.orm import Session

from app.models.projects import Project
from app.models.user import User

from app.core.exceptions import (
    ProjectNotFoundException
)
from app.services.Gns3.Projects import (
    create_gns3_project,
    open_gns3_project,
    open_gns3_project,
    close_gns3_project,
     delete_gns3_project
)

##########################Get Project By Id
def get_project_by_id(
    db: Session,
    project_id: int,
    current_user: User
) -> Project:

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise ProjectNotFoundException(
            "Project not found"
        )

    return project
##########################

##########################Create Project
async def create_project(
    db: Session,
    name: str,
    current_user: User
) -> Project:

    gns3_project = await create_gns3_project(
        name
    )

    project = Project(
        name=name,
        project_id=gns3_project["project_id"],
        owner_id=current_user.id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project
##########################

#########################get User's Project
def get_user_projects(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20
) -> list[Project]:

    query = (
        db.query(Project)
        .filter(
            Project.owner_id == current_user.id
        )
        .order_by(
            Project.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    return query.all()
#########################

#########################Open Project
async def open_project(
    db: Session,
    project_id: int,
    current_user: User
) -> Project:

    project = get_project_by_id(
    db=db,
    project_id=project_id,
    current_user=current_user
)

    if not project:
        raise ProjectNotFoundException(
            "Project not found"
        )

    await open_gns3_project(
        str(project.project_id)
    )

    return project
#########################

#########################Close Project
async def close_project(
    db: Session,
    project_id: int,
    current_user: User
) -> Project:

    project = get_project_by_id(
    db=db,
    project_id=project_id,
    current_user=current_user
)

    if not project:
        raise ProjectNotFoundException(
            "Project not found"
        )

    await close_gns3_project(
        str(project.project_id)
    )

    return project
#########################

#########################Delete Project
async def delete_project(
    db: Session,
    project_id: int,
    current_user: User
) -> None:

    project = get_project_by_id(
    db=db,
    project_id=project_id,
    current_user=current_user
)

    if not project:
        raise ProjectNotFoundException(
            "Project not found"
        )

    await delete_gns3_project(
        str(project.project_id)
    )

    db.delete(project)
    db.commit()
#########################