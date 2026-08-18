import re
from ipaddress import IPv4Address

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConnectivityResultParseException,
    DeviceTypeUndeterminedException,
    InterfaceDiscoveryParseException,
    NetmikoUnreachableException,
    UnsupportedAutomationException,
)
from app.models.user import User
from app.schemas.connectivity import (
    ConnectivityDiscoveryNodeResult,
    DiscoveredInterface,
)
from app.services.Automation.parsers.interface import parse_cisco_interface_brief
from app.services.Automation.catalog import validate_automation_for_device
from app.services.Netmiko.command import run_commands
from app.services.deviceClassificationService import get_node_device_type
from app.services.nodeService import get_node_console
from app.services.nodeService import get_nodes as get_project_nodes


SUCCESS_RATE_PATTERN = re.compile(
    r"Success\s+rate\s+is\s+(\d+)\s+percent\s+\(\d+/\d+\)",
    re.IGNORECASE,
)
LATENCY_PATTERN = re.compile(
    r"min/avg/max\s*=\s*[\d.]+/([\d.]+)/[\d.]+\s*ms",
    re.IGNORECASE,
)


def parse_cisco_ping_output(output: str) -> tuple[bool, int, float | None]:
    """Normalize Cisco IOS ping output without inferring an unparsed result."""
    success_match = SUCCESS_RATE_PATTERN.search(output)
    if not success_match:
        raise ConnectivityResultParseException(
            "The device ping result could not be determined."
        )

    success_rate = int(success_match.group(1))
    if not 0 <= success_rate <= 100:
        raise ConnectivityResultParseException(
            "The device ping result could not be determined."
        )

    latency_match = LATENCY_PATTERN.search(output)
    latency_ms = float(latency_match.group(1)) if latency_match else None

    return success_rate > 0, 100 - success_rate, latency_ms


async def run_node_ping(
    db: Session,
    project_id: int,
    node_id: str,
    destination: IPv4Address,
    current_user: User,
) -> dict:
    """Ping a validated IPv4 destination from a supported Cisco IOS node."""
    device_type = await get_node_device_type(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )
    validate_automation_for_device("ping", device_type)

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )

    command = f"ping {destination}"
    results = await run_commands(
        host=console_host,
        port=console_port,
        commands=[command],
        timeout=30,
    )
    output = results.get(command, "")
    reachable, packet_loss_percent, latency_ms = parse_cisco_ping_output(output)

    return {
        "source_node_id": node_id,
        "destination": destination,
        "reachable": reachable,
        "packet_loss_percent": packet_loss_percent,
        "latency_ms": latency_ms,
    }


async def discover_node_interfaces(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
    node_name: str | None = None,
) -> list[DiscoveredInterface]:
    """Discover current primary IPv4 interface state from one supported node."""
    device_type = await get_node_device_type(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )
    validate_automation_for_device("discover_interfaces", device_type)

    console_host, console_port = await get_node_console(
        db=db,
        project_id=project_id,
        node_id=node_id,
        current_user=current_user,
    )
    command = "show ip interface brief"
    results = await run_commands(
        host=console_host,
        port=console_port,
        commands=[command],
        timeout=30,
    )
    rows = parse_cisco_interface_brief(results.get(command, ""))

    return [
        DiscoveredInterface(
            node_id=node_id,
            node_name=node_name or node_id,
            **row,
        )
        for row in rows
    ]


async def discover_project_interfaces(
    db: Session,
    project_id: int,
    current_user: User,
) -> dict:
    """Discover interfaces sequentially and preserve per-node nonfatal results."""
    nodes = await get_project_nodes(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )
    endpoints: list[DiscoveredInterface] = []
    node_results: list[ConnectivityDiscoveryNodeResult] = []

    for node in nodes:
        node_id = node["node_id"]
        node_name = node.get("name", node_id)
        try:
            discovered = await discover_node_interfaces(
                db=db,
                project_id=project_id,
                node_id=node_id,
                current_user=current_user,
                node_name=node_name,
            )
        except DeviceTypeUndeterminedException:
            node_results.append(
                ConnectivityDiscoveryNodeResult(
                    node_id=node_id,
                    node_name=node_name,
                    state="skipped",
                    reason="device_type_undetermined",
                )
            )
        except UnsupportedAutomationException:
            node_results.append(
                ConnectivityDiscoveryNodeResult(
                    node_id=node_id,
                    node_name=node_name,
                    state="skipped",
                    reason="unsupported_device_type",
                )
            )
        except NetmikoUnreachableException:
            node_results.append(
                ConnectivityDiscoveryNodeResult(
                    node_id=node_id,
                    node_name=node_name,
                    state="error",
                    reason="device_unavailable",
                )
            )
        except InterfaceDiscoveryParseException:
            node_results.append(
                ConnectivityDiscoveryNodeResult(
                    node_id=node_id,
                    node_name=node_name,
                    state="error",
                    reason="interface_parse_failed",
                )
            )
        else:
            endpoints.extend(discovered)
            node_results.append(
                ConnectivityDiscoveryNodeResult(
                    node_id=node_id,
                    node_name=node_name,
                    state="discovered",
                )
            )

    return {"endpoints": endpoints, "node_results": node_results}
