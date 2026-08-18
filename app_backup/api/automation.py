from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import (
    ProjectNotFoundException,
    NetmikoUnreachableException,
    NetmikoAuthException,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.automation import (
    CommandRequest,
    CommandResponse,
    ConfigureRequest,
    ConfigureResponse,
)
from app.services import automationService
from app.schemas.automation_vlan import VlanCreateRequest, VlanCreateResponse
router = APIRouter(
    prefix="/projects/{project_id}/nodes/{node_id}",
    tags=["Automation"],
)


########################## Run Commands ##########################
@router.post(
    "/commands",
    response_model=CommandResponse,
)
async def run_commands(
    project_id: int,
    node_id: str,
    payload: CommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        results = await automationService.run_node_commands(
            db=db,
            project_id=project_id,
            node_id=node_id,
            commands=payload.commands,
            current_user=current_user,
            secret=payload.secret,
        )
        return {"results": results}
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except NetmikoAuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except NetmikoUnreachableException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
####################################################################

########################## Run Configure ##########################
@router.post(
    "/configure",
    response_model=ConfigureResponse,
)
async def run_configure(
    project_id: int,
    node_id: str,
    payload: ConfigureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        output = await automationService.run_node_configure(
            db=db,
            project_id=project_id,
            node_id=node_id,
            commands=payload.commands,
            current_user=current_user,
            secret=payload.secret,
        )
        return {"output": output}
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except NetmikoAuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except NetmikoUnreachableException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
##################################################################
########################## Create VLAN ##########################
@router.post(
    "/automation/vlan",
    response_model=VlanCreateResponse,
)
async def create_vlan(
    project_id: int,
    node_id: str,
    payload: VlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        output = await automationService.run_node_vlan(
            db=db,
            project_id=project_id,
            node_id=node_id,
            vlan_id=payload.vlan_id,
            name=payload.name,
            interface=payload.interface,
            current_user=current_user,
            secret=payload.secret,
        )
        return {"output": output}
    except ProjectNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except NetmikoAuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except NetmikoUnreachableException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
##################################################################