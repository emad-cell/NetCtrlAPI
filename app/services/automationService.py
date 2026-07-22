from sqlalchemy.orm import Session

from app.models.user import User
from app.services.nodeService import get_node_console
from app.services.Netmiko.command import run_commands
from app.services.Netmiko.config import run_config
from app.services.Automation.vlan import build_vlan_commands

########################## Run Commands ##########################
async def run_node_commands(
    db: Session,
    project_id: int,
    node_id: str,
    commands: list[str],
    current_user: User,
    secret: str = "",
) -> dict[str, str]:

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