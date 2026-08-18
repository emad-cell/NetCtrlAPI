from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import (
    ProjectNotFoundException,
    NetmikoUnreachableException,
    NetmikoAuthException,
    DeviceTypeUndeterminedException,
    UnsupportedAutomationException,
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
from app.schemas.automation_interface import InterfaceIpRequest, InterfaceIpResponse
from app.schemas.automation_ospf import OspfCreateRequest, OspfCreateResponse
from app.schemas.automation_static_route import StaticRouteCreateRequest, StaticRouteCreateResponse
from app.schemas.automation_catalog import AutomationTask
from app.services.Automation.catalog import get_catalog

router = APIRouter(
    prefix="/projects/{project_id}/nodes/{node_id}",
    tags=["Automation"],
)

catalog_router = APIRouter(
    prefix="/automation",
    tags=["Automation"],
)


def _raise_automation_http_error(exc: Exception) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


########################## Get Catalog ##########################
@catalog_router.get(
    "/catalog",
    response_model=list[AutomationTask],
)
async def list_automation_tasks(
    current_user: User = Depends(get_current_user),
):
    return get_catalog()
####################################################################


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
    except (DeviceTypeUndeterminedException, UnsupportedAutomationException) as e:
        _raise_automation_http_error(e)
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
    except (DeviceTypeUndeterminedException, UnsupportedAutomationException) as e:
        _raise_automation_http_error(e)
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
    except (DeviceTypeUndeterminedException, UnsupportedAutomationException) as e:
        _raise_automation_http_error(e)
##################################################################
########################## Set Interface IP ##########################
@router.post(
    "/automation/interface-ip",
    response_model=InterfaceIpResponse,
)
async def set_interface_ip(
    project_id: int,
    node_id: str,
    payload: InterfaceIpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        output = await automationService.run_node_interface_ip(
            db=db,
            project_id=project_id,
            node_id=node_id,
            interface=payload.interface,
            ip_address=payload.ip_address,
            subnet_mask=payload.subnet_mask,
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
    except (DeviceTypeUndeterminedException, UnsupportedAutomationException) as e:
        _raise_automation_http_error(e)
########################################################################

########################## Create OSPF ##########################
@router.post(
    "/automation/ospf",
    response_model=OspfCreateResponse,
)
async def create_ospf(
    project_id: int,
    node_id: str,
    payload: OspfCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        output = await automationService.run_node_ospf(
            db=db,
            project_id=project_id,
            node_id=node_id,
            process_id=payload.process_id,
            network=payload.network,
            wildcard=payload.wildcard,
            area=payload.area,
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
    except (DeviceTypeUndeterminedException, UnsupportedAutomationException) as e:
        _raise_automation_http_error(e)
####################################################################

########################## Create Static Route ##########################
@router.post(
    "/automation/static-route",
    response_model=StaticRouteCreateResponse,
)
async def create_static_route(
    project_id: int,
    node_id: str,
    payload: StaticRouteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        output = await automationService.run_node_static_route(
            db=db,
            project_id=project_id,
            node_id=node_id,
            destination=payload.destination,
            subnet_mask=payload.subnet_mask,
            next_hop=payload.next_hop,
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
    except (DeviceTypeUndeterminedException, UnsupportedAutomationException) as e:
        _raise_automation_http_error(e)
############################################################################
