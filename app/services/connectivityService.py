import re
from ipaddress import IPv4Address

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConnectivityResultParseException,
    DeviceTypeUndeterminedException,
    InterfaceDiscoveryParseException,
    NetmikoAuthException,
    NetmikoUnreachableException,
    UnsupportedAutomationException,
)
from app.models.user import User
from app.schemas.connectivity import (
    ConnectivityCheckResult,
    ConnectivityDiscoveryNodeResult,
    DiscoveredInterface,
)
from app.services.Automation.parsers.interface import parse_cisco_interface_brief
from app.services.Automation.catalog import validate_automation_for_device
from app.services.Netmiko.command import run_commands
from app.services.deviceClassificationService import get_node_device_type
from app.services.nodeService import get_node_console
from app.services.nodeService import get_nodes as get_project_nodes
from app.services.linkService import get_links as get_project_links


SUCCESS_RATE_PATTERN = re.compile(
    r"Success\s+rate\s+is\s+(\d+)\s+percent\s+\(\d+/\d+\)",
    re.IGNORECASE,
)
LATENCY_PATTERN = re.compile(
    r"min/avg/max\s*=\s*[\d.]+/([\d.]+)/[\d.]+\s*ms",
    re.IGNORECASE,
)

COMMAND_INTERFACE_BRIEF = "show ip interface brief"


def _node_port_name_map(node: dict) -> dict[tuple[int, int], str]:
    """Return only explicit GNS3 adapter/port -> interface mappings.

    GNS3 node payloads may expose a ``ports`` collection containing the IOS
    interface name together with adapter/port numbers. If that metadata is
    absent or incomplete, we deliberately return no mapping instead of
    guessing from numeric indexes.
    """
    mapping: dict[tuple[int, int], str] = {}
    ports = node.get("ports")
    if not isinstance(ports, list):
        return mapping

    for port in ports:
        if not isinstance(port, dict):
            continue
        name = port.get("name")
        adapter = port.get("adapter_number")
        port_number = port.get("port_number")
        if not isinstance(name, str) or not name:
            continue
        if not isinstance(adapter, int) or not isinstance(port_number, int):
            continue
        mapping[(adapter, port_number)] = name

    return mapping


def _resolve_link_interface(
    node: dict,
    adapter: int,
    port: int,
    discovered: list[DiscoveredInterface],
) -> DiscoveredInterface | None:
    interface_name = _node_port_name_map(node).get((adapter, port))
    if interface_name is None:
        return None

    return next(
        (item for item in discovered if item.interface == interface_name),
        None,
    )


def _is_pingable_interface(interface: DiscoveredInterface) -> bool:
    return (
        interface.ip_address is not None
        and interface.status == "up"
        and interface.protocol == "up"
    )


def _check_result_from_ping(
    source: DiscoveredInterface,
    destination: DiscoveredInterface,
    ping_result: dict,
) -> ConnectivityCheckResult:
    reachable = ping_result["reachable"]
    return ConnectivityCheckResult(
        source_node_id=source.node_id,
        source_interface=source.interface,
        destination_node_id=destination.node_id,
        destination_interface=destination.interface,
        destination_ip=destination.ip_address,
        state="reachable" if reachable else "unreachable",
        packet_loss_percent=ping_result.get("packet_loss_percent"),
        latency_ms=ping_result.get("latency_ms"),
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
    command = COMMAND_INTERFACE_BRIEF
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


async def check_project_connectivity(
    db: Session,
    project_id: int,
    current_user: User,
) -> dict:
    """Check L3 reachability across unambiguous physical neighbor links.

    Only endpoints with a discovered IPv4 address and up/up state are
    attempted. GNS3 adapter/port pairs are used only when the node payload
    explicitly maps them to an interface name. Ambiguous links are skipped.
    Checks are sequential and bidirectional per valid link.
    """
    nodes = await get_project_nodes(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    node_by_id = {node["node_id"]: node for node in nodes}
    discovered_by_node: dict[str, list[DiscoveredInterface]] = {}
    node_failure: dict[str, tuple[str, str]] = {}

    for node in nodes:
        node_id = node["node_id"]
        node_name = node.get("name", node_id)
        try:
            discovered_by_node[node_id] = await discover_node_interfaces(
                db=db,
                project_id=project_id,
                node_id=node_id,
                current_user=current_user,
                node_name=node_name,
            )
        except DeviceTypeUndeterminedException:
            node_failure[node_id] = ("skipped", "device_type_undetermined")
        except UnsupportedAutomationException:
            node_failure[node_id] = ("skipped", "unsupported_device_type")
        except NetmikoAuthException:
            node_failure[node_id] = ("error", "authentication_failed")
        except NetmikoUnreachableException:
            node_failure[node_id] = ("error", "device_unavailable")
        except InterfaceDiscoveryParseException:
            node_failure[node_id] = ("error", "interface_parse_failed")

    links = await get_project_links(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )

    results: list[ConnectivityCheckResult] = []

    for link in links:
        endpoints = link.get("nodes", []) if isinstance(link, dict) else []
        if not isinstance(endpoints, list) or len(endpoints) != 2:
            continue

        left, right = endpoints
        if not isinstance(left, dict) or not isinstance(right, dict):
            continue

        pairs = ((left, right), (right, left))
        for source_endpoint, destination_endpoint in pairs:
            source_id = source_endpoint.get("node_id")
            destination_id = destination_endpoint.get("node_id")
            if source_id not in node_by_id or destination_id not in node_by_id:
                continue

            source_failure = node_failure.get(source_id)
            if source_failure:
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        state=source_failure[0],
                        reason=source_failure[1],
                    )
                )
                continue

            destination_failure = node_failure.get(destination_id)
            if destination_failure:
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        state="skipped",
                        reason=destination_failure[1],
                    )
                )
                continue

            source_interface = _resolve_link_interface(
                node_by_id[source_id],
                source_endpoint.get("adapter_number"),
                source_endpoint.get("port_number"),
                discovered_by_node[source_id],
            )
            destination_interface = _resolve_link_interface(
                node_by_id[destination_id],
                destination_endpoint.get("adapter_number"),
                destination_endpoint.get("port_number"),
                discovered_by_node[destination_id],
            )

            if source_interface is None or destination_interface is None:
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        source_interface=(source_interface.interface if source_interface else None),
                        destination_node_id=destination_id,
                        destination_interface=(destination_interface.interface if destination_interface else None),
                        state="skipped",
                        reason="interface_mapping_ambiguous",
                    )
                )
                continue

            if not _is_pingable_interface(source_interface):
                reason = (
                    "no_ip_address"
                    if source_interface.ip_address is None
                    else "administratively_down"
                    if source_interface.status == "administratively down"
                    else "protocol_down"
                )
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        source_interface=source_interface.interface,
                        destination_node_id=destination_id,
                        destination_interface=destination_interface.interface,
                        destination_ip=destination_interface.ip_address,
                        state="skipped",
                        reason=reason,
                    )
                )
                continue

            if not _is_pingable_interface(destination_interface):
                reason = (
                    "no_ip_address"
                    if destination_interface.ip_address is None
                    else "administratively_down"
                    if destination_interface.status == "administratively down"
                    else "protocol_down"
                )
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        source_interface=source_interface.interface,
                        destination_node_id=destination_id,
                        destination_interface=destination_interface.interface,
                        destination_ip=destination_interface.ip_address,
                        state="skipped",
                        reason=reason,
                    )
                )
                continue

            try:
                ping_result = await run_node_ping(
                    db=db,
                    project_id=project_id,
                    node_id=source_id,
                    destination=destination_interface.ip_address,
                    current_user=current_user,
                )
            except NetmikoAuthException:
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        source_interface=source_interface.interface,
                        destination_node_id=destination_id,
                        destination_interface=destination_interface.interface,
                        destination_ip=destination_interface.ip_address,
                        state="error",
                        reason="authentication_failed",
                    )
                )
                continue
            except NetmikoUnreachableException:
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        source_interface=source_interface.interface,
                        destination_node_id=destination_id,
                        destination_interface=destination_interface.interface,
                        destination_ip=destination_interface.ip_address,
                        state="error",
                        reason="device_unavailable",
                    )
                )
                continue
            except ConnectivityResultParseException:
                results.append(
                    ConnectivityCheckResult(
                        source_node_id=source_id,
                        source_interface=source_interface.interface,
                        destination_node_id=destination_id,
                        destination_interface=destination_interface.interface,
                        destination_ip=destination_interface.ip_address,
                        state="error",
                        reason="ping_parse_failed",
                    )
                )
                continue

            results.append(
                _check_result_from_ping(
                    source_interface,
                    destination_interface,
                    ping_result,
                )
            )

    return {"results": results}
