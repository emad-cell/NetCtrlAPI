from app.schemas.automation_catalog import AutomationTask, AutomationParam
from app.core.exceptions import UnsupportedAutomationException


CATALOG: list[AutomationTask] = [
    AutomationTask(
        id="discover_interfaces",
        name="Discover Interfaces",
        description="Discover current IPv4 interface state from this device.",
        category="Discovery",
        endpoint="/projects/{project_id}/connectivity/endpoints",
        supported_device_types=["router", "switch"],
        params=[],
    ),
    AutomationTask(
        id="check_connectivity",
        name="Check Project Connectivity",
        description="Check IPv4 reachability across unambiguous physical neighbor links.",
        category="Connectivity",
        endpoint="/projects/{project_id}/connectivity/check",
        supported_device_types=["router", "switch"],
        params=[],
    ),
    AutomationTask(
        id="ping",
        name="Ping",
        description="Test IPv4 reachability from this device.",
        category="Connectivity",
        endpoint="/projects/{project_id}/nodes/{node_id}/connectivity/ping",
        supported_device_types=["router", "switch"],
        params=[
            AutomationParam(name="destination", label="Destination IPv4 Address", type="string", placeholder="10.0.0.2"),
        ],
    ),
    AutomationTask(
        id="interface_ip",
        name="Configure Interface IP",
        description="Assign an IP address to an interface and bring it up.",
        category="Interface",
        endpoint="/projects/{project_id}/nodes/{node_id}/automation/interface-ip",
        supported_device_types=["router"],
        params=[
            AutomationParam(name="interface", label="Interface", type="string", placeholder="FastEthernet0/0"),
            AutomationParam(name="ip_address", label="IP Address", type="string", placeholder="10.0.0.1"),
            AutomationParam(name="subnet_mask", label="Subnet Mask", type="string", placeholder="255.255.255.0"),
            AutomationParam(name="secret", label="Enable Secret", type="string", required=False),
        ],
    ),
    AutomationTask(
        id="create_vlan",
        name="Create VLAN",
        description="Create a VLAN and optionally assign it to an interface. Requires a Layer 2 capable device.",
        category="VLAN",
        endpoint="/projects/{project_id}/nodes/{node_id}/automation/vlan",
        supported_device_types=["switch"],
        params=[
            AutomationParam(name="vlan_id", label="VLAN ID", type="int", placeholder="10"),
            AutomationParam(name="name", label="VLAN Name", type="string", placeholder="SALES"),
            AutomationParam(name="interface", label="Interface", type="string", required=False, placeholder="FastEthernet0/1"),
            AutomationParam(name="secret", label="Enable Secret", type="string", required=False),
        ],
    ),
    AutomationTask(
        id="create_ospf",
        name="Configure OSPF",
        description="Enable OSPF routing and advertise a network into an area.",
        category="Routing",
        endpoint="/projects/{project_id}/nodes/{node_id}/automation/ospf",
        supported_device_types=["router"],
        params=[
            AutomationParam(name="process_id", label="Process ID", type="int", placeholder="1"),
            AutomationParam(name="network", label="Network", type="string", placeholder="10.0.0.0"),
            AutomationParam(name="wildcard", label="Wildcard Mask", type="string", placeholder="0.0.0.255"),
            AutomationParam(name="area", label="Area", type="int", placeholder="0"),
            AutomationParam(name="secret", label="Enable Secret", type="string", required=False),
        ],
    ),
    AutomationTask(
        id="create_static_route",
        name="Create Static Route",
        description="Add a static route pointing to a next-hop address.",
        category="Routing",
        endpoint="/projects/{project_id}/nodes/{node_id}/automation/static-route",
        supported_device_types=["router"],
        params=[
            AutomationParam(name="destination", label="Destination Network", type="string", placeholder="192.168.2.0"),
            AutomationParam(name="subnet_mask", label="Subnet Mask", type="string", placeholder="255.255.255.0"),
            AutomationParam(name="next_hop", label="Next Hop IP", type="string", placeholder="10.0.0.2"),
            AutomationParam(name="secret", label="Enable Secret", type="string", required=False),
        ],
    ),
    AutomationTask(
        id="run_command",
        name="Run Show Command",
        description="Execute one or more read-only show commands on a supported router or switch.",
        category="Diagnostics",
        endpoint="/projects/{project_id}/nodes/{node_id}/commands",
        supported_device_types=["router", "switch"],
        params=[
            AutomationParam(name="commands", label="Commands (one per line)", type="string"),
        ],
    ),
    AutomationTask(
        id="run_configure",
        name="Run Raw Configuration",
        description="Execute one or more raw configuration commands on the device.",
        category="Configuration",
        endpoint="/projects/{project_id}/nodes/{node_id}/configure",
        supported_device_types=["router", "switch"],
        params=[
            AutomationParam(name="commands", label="Commands (one per line)", type="string"),
            AutomationParam(name="secret", label="Enable Secret", type="string", required=False),
        ],
    ),
]


def get_catalog() -> list[AutomationTask]:
    return CATALOG


def validate_automation_for_device(
    automation_id: str,
    device_type: str,
) -> None:
    task = next((task for task in CATALOG if task.id == automation_id), None)

    if task is None or device_type not in task.supported_device_types:
        raise UnsupportedAutomationException(
            f"Automation '{automation_id}' is not supported for device type "
            f"'{device_type}'."
        )
