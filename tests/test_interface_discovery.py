import unittest
from ipaddress import IPv4Address
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.core.exceptions import (
    DeviceTypeUndeterminedException,
    GNS3UnreachableException,
    InterfaceDiscoveryParseException,
    NetmikoUnreachableException,
    UnsupportedAutomationException,
)
from app.services import connectivityService
from app.services.Automation.catalog import get_catalog, validate_automation_for_device
from app.services.Automation.parsers.interface import parse_cisco_interface_brief


INTERFACE_BRIEF_OUTPUT = """Interface              IP-Address      OK? Method Status                Protocol
FastEthernet0/0        10.0.0.1        YES manual up                    up
FastEthernet0/1        unassigned      YES unset  administratively down down
Serial1/0              10.0.1.1        YES manual down                  down
"""


class InterfaceBriefParserTests(unittest.TestCase):
    def test_parses_multiple_interface_states(self):
        interfaces = parse_cisco_interface_brief(INTERFACE_BRIEF_OUTPUT)

        self.assertEqual(len(interfaces), 3)
        self.assertEqual(interfaces[0]["ip_address"], IPv4Address("10.0.0.1"))
        self.assertIsNone(interfaces[1]["ip_address"])
        self.assertEqual(interfaces[1]["status"], "administratively down")
        self.assertEqual(interfaces[2]["status"], "down")
        self.assertEqual(interfaces[2]["protocol"], "down")

    def test_rejects_header_only_output(self):
        with self.assertRaises(InterfaceDiscoveryParseException):
            parse_cisco_interface_brief(
                "Interface              IP-Address      OK? Method Status                Protocol"
            )

    def test_rejects_malformed_row(self):
        with self.assertRaises(InterfaceDiscoveryParseException):
            parse_cisco_interface_brief(
                "Interface              IP-Address      OK? Method Status                Protocol\n"
                "FastEthernet0/0 malformed row"
            )


class InterfaceDiscoveryCatalogTests(unittest.TestCase):
    def test_discovery_capability_supports_router_and_switch_only(self):
        discovery = next(task for task in get_catalog() if task.id == "discover_interfaces")
        self.assertEqual(discovery.supported_device_types, ["router", "switch"])
        validate_automation_for_device("discover_interfaces", "router")
        validate_automation_for_device("discover_interfaces", "switch")
        with self.assertRaises(UnsupportedAutomationException):
            validate_automation_for_device("discover_interfaces", "host")


class NodeInterfaceDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_router_discovery_returns_normalized_interfaces(self):
        command = "show ip interface brief"
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="router"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock, return_value={command: INTERFACE_BRIEF_OUTPUT}) as run_commands,
        ):
            interfaces = await connectivityService.discover_node_interfaces(
                db=None,
                project_id=1,
                node_id="router-1",
                node_name="R1",
                current_user=None,
            )

        self.assertEqual(interfaces[0].node_name, "R1")
        self.assertEqual(interfaces[0].interface, "FastEthernet0/0")
        self.assertEqual(interfaces[0].ip_address, IPv4Address("10.0.0.1"))
        self.assertEqual(run_commands.await_args.kwargs["commands"], [command])

    async def test_switch_discovery_is_supported(self):
        command = "show ip interface brief"
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="switch"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock, return_value={command: INTERFACE_BRIEF_OUTPUT}),
        ):
            interfaces = await connectivityService.discover_node_interfaces(
                db=None,
                project_id=1,
                node_id="switch-1",
                current_user=None,
            )

        self.assertEqual(len(interfaces), 3)

    async def test_host_is_rejected_before_console_or_netmiko(self):
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="host"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock) as run_commands,
        ):
            with self.assertRaises(UnsupportedAutomationException):
                await connectivityService.discover_node_interfaces(None, 1, "host-1", None)

        get_console.assert_not_awaited()
        run_commands.assert_not_awaited()

    async def test_unknown_device_is_rejected_before_console_or_netmiko(self):
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, side_effect=DeviceTypeUndeterminedException("unknown")),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock) as run_commands,
        ):
            with self.assertRaises(DeviceTypeUndeterminedException):
                await connectivityService.discover_node_interfaces(None, 1, "unknown-1", None)

        get_console.assert_not_awaited()
        run_commands.assert_not_awaited()

    async def test_supported_discovery_orders_validation_before_console_and_netmiko(self):
        calls = []
        original_validate = connectivityService.validate_automation_for_device
        command = "show ip interface brief"

        async def classify(*args, **kwargs):
            calls.append("classification")
            return "router"

        def validate(*args, **kwargs):
            calls.append("validation")
            return original_validate(*args, **kwargs)

        async def console(*args, **kwargs):
            calls.append("console")
            return "127.0.0.1", 5000

        async def netmiko(*args, **kwargs):
            calls.append("netmiko")
            return {command: INTERFACE_BRIEF_OUTPUT}

        with (
            patch.object(connectivityService, "get_node_device_type", side_effect=classify),
            patch.object(connectivityService, "validate_automation_for_device", side_effect=validate),
            patch.object(connectivityService, "get_node_console", side_effect=console),
            patch.object(connectivityService, "run_commands", side_effect=netmiko),
        ):
            await connectivityService.discover_node_interfaces(None, 1, "router-1", None)

        self.assertEqual(calls, ["classification", "validation", "console", "netmiko"])

    async def test_netmiko_and_parser_errors_are_preserved(self):
        command = "show ip interface brief"
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="router"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock, side_effect=NetmikoUnreachableException("refused")),
        ):
            with self.assertRaises(NetmikoUnreachableException):
                await connectivityService.discover_node_interfaces(None, 1, "router-1", None)

        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="router"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock, return_value={command: "bad output"}),
        ):
            with self.assertRaises(InterfaceDiscoveryParseException):
                await connectivityService.discover_node_interfaces(None, 1, "router-1", None)


class ProjectInterfaceDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_aggregates_success_and_unsupported_skip(self):
        nodes = [
            {"node_id": "router-1", "name": "R1"},
            {"node_id": "host-1", "name": "PC1"},
        ]
        discovered = [
            connectivityService.DiscoveredInterface(
                node_id="router-1",
                node_name="R1",
                interface="FastEthernet0/0",
                ip_address=IPv4Address("10.0.0.1"),
                status="up",
                protocol="up",
            )
        ]

        async def discover(*args, **kwargs):
            if kwargs["node_id"] == "host-1":
                raise UnsupportedAutomationException("unsupported")
            return discovered

        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", side_effect=discover),
        ):
            result = await connectivityService.discover_project_interfaces(None, 1, None)

        self.assertEqual(result["endpoints"], discovered)
        self.assertEqual(result["node_results"][0].state, "discovered")
        self.assertEqual(result["node_results"][1].reason, "unsupported_device_type")

    async def test_unavailable_node_does_not_stop_other_nodes(self):
        nodes = [
            {"node_id": "router-1", "name": "R1"},
            {"node_id": "router-2", "name": "R2"},
        ]
        discovered = [
            connectivityService.DiscoveredInterface(
                node_id="router-2",
                node_name="R2",
                interface="FastEthernet0/0",
                ip_address=IPv4Address("10.0.0.2"),
                status="up",
                protocol="up",
            )
        ]

        async def discover(*args, **kwargs):
            if kwargs["node_id"] == "router-1":
                raise NetmikoUnreachableException("refused")
            return discovered

        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", side_effect=discover),
        ):
            result = await connectivityService.discover_project_interfaces(None, 1, None)

        self.assertEqual(result["node_results"][0].reason, "device_unavailable")
        self.assertEqual(result["endpoints"], discovered)

    async def test_unknown_node_is_skipped_without_stopping_discovery(self):
        nodes = [
            {"node_id": "unknown-1", "name": "Unknown"},
            {"node_id": "router-1", "name": "R1"},
        ]

        async def discover(*args, **kwargs):
            if kwargs["node_id"] == "unknown-1":
                raise DeviceTypeUndeterminedException("unknown")
            return []

        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", side_effect=discover),
        ):
            result = await connectivityService.discover_project_interfaces(None, 1, None)

        self.assertEqual(result["node_results"][0].reason, "device_type_undetermined")
        self.assertEqual(result["node_results"][1].state, "discovered")

    async def test_gns3_infrastructure_failure_is_not_aggregated_as_node_error(self):
        nodes = [{"node_id": "router-1", "name": "R1"}]
        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", new_callable=AsyncMock, side_effect=GNS3UnreachableException("timed out")),
        ):
            with self.assertRaises(GNS3UnreachableException):
                await connectivityService.discover_project_interfaces(None, 1, None)
