from sqlalchemy.orm import Session

from app.models.user import User
from app.services.nodeService import get_node_console
from app.services.Netmiko.command import run_commands
from app.services.Netmiko.config import run_config
from app.services.Automation.vlan import build_vlan_commands
from app.services.Automation.interface import build_interface_ip_commands
from app.services.Automation.ospf import build_ospf_commands
from app.services.Automation.static_route import build_static_route_commands
from app.services.Automation.catalog import validate_automation_for_device
from app.services.deviceClassificationService import get_node_device_type


async def _validate_node_automation(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
    automation_id: str,
) -> None:
    device_type = await get_node_device_type(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )
    validate_automation_for_device(automation_id, device_type)

########################## Run Commands ##########################
async def run_node_commands(
    db: Session,
    project_id: int,
    node_id: str,
    commands: list[str],
    current_user: User,
    secret: str = "",
) -> dict[str, str]:

    await _validate_node_automation(
        db, project_id, node_id, current_user, "run_command"
    )

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    return await run_commands(
        host=console_host,
        port=console_port,
        commands=commands,
        secret=secret,
    )
####################################################################

########################## Run Configure ##########################
async def run_node_configure(
    db: Session,
    project_id: int,
    node_id: str,
    commands: list[str],
    current_user: User,
    secret: str = "",
) -> str:

    await _validate_node_automation(
        db, project_id, node_id, current_user, "run_configure"
    )

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    return await run_config(
        host=console_host,
        port=console_port,
        commands=commands,
        secret=secret,
    )
##################################################################
########################## Create VLAN ##########################
async def run_node_vlan(
    db: Session,
    project_id: int,
    node_id: str,
    vlan_id: int,
    name: str,
    current_user: User,
    interface: str | None = None,
    secret: str = "",
) -> str:

    await _validate_node_automation(
        db, project_id, node_id, current_user, "create_vlan"
    )

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    commands = build_vlan_commands(
        vlan_id=vlan_id,
        name=name,
        interface=interface,
    )

    return await run_config(
        host=console_host,
        port=console_port,
        commands=commands,
        secret=secret,
    )
##################################################################
########################## Set Interface IP ##########################
async def run_node_interface_ip(
    db: Session,
    project_id: int,
    node_id: str,
    interface: str,
    ip_address: str,
    subnet_mask: str,
    current_user: User,
    secret: str = "",
) -> str:

    await _validate_node_automation(
        db, project_id, node_id, current_user, "interface_ip"
    )

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    commands = build_interface_ip_commands(
        interface=interface,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
    )

    return await run_config(
        host=console_host,
        port=console_port,
        commands=commands,
        secret=secret,
    )
########################################################################

########################## Create OSPF ##########################
async def run_node_ospf(
    db: Session,
    project_id: int,
    node_id: str,
    process_id: int,
    network: str,
    wildcard: str,
    area: int,
    current_user: User,
    secret: str = "",
) -> str:

    await _validate_node_automation(
        db, project_id, node_id, current_user, "create_ospf"
    )

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    commands = build_ospf_commands(
        process_id=process_id,
        network=network,
        wildcard=wildcard,
        area=area,
    )

    return await run_config(
        host=console_host,
        port=console_port,
        commands=commands,
        secret=secret,
    )
####################################################################

########################## Create Static Route ##########################
async def run_node_static_route(
    db: Session,
    project_id: int,
    node_id: str,
    destination: str,
    subnet_mask: str,
    next_hop: str,
    current_user: User,
    secret: str = "",
) -> str:

    await _validate_node_automation(
        db, project_id, node_id, current_user, "create_static_route"
    )

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    commands = build_static_route_commands(
        destination=destination,
        subnet_mask=subnet_mask,
        next_hop=next_hop,
    )

    return await run_config(
        host=console_host,
        port=console_port,
        commands=commands,
        secret=secret,
    )
############################################################################
