import unittest
from ipaddress import IPv4Address
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.api import connectivity
from app.core.exceptions import (
    ConnectivityResultParseException,
    DeviceTypeUndeterminedException,
    GNS3UnreachableException,
    NetmikoUnreachableException,
    UnsupportedAutomationException,
)
from app.schemas.connectivity import PingRequest
from app.services import connectivityService
from app.services.Automation.catalog import get_catalog, validate_automation_for_device


class PingSchemaTests(unittest.TestCase):
    def test_accepts_valid_ipv4_destination(self):
        request = PingRequest(destination="10.0.0.2")
        self.assertEqual(request.destination, IPv4Address("10.0.0.2"))

    def test_rejects_invalid_destination(self):
        with self.assertRaises(ValidationError):
            PingRequest(destination="not-an-ip-address")


class CiscoPingParserTests(unittest.TestCase):
    def test_parses_full_success_and_average_latency(self):
        result = connectivityService.parse_cisco_ping_output(
            "Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms"
        )
        self.assertEqual(result, (True, 0, 2.0))

    def test_parses_unreachable_destination(self):
        result = connectivityService.parse_cisco_ping_output(
            "Success rate is 0 percent (0/5)"
        )
        self.assertEqual(result, (False, 100, None))

    def test_parses_partial_success(self):
        result = connectivityService.parse_cisco_ping_output(
            "Success rate is 80 percent (4/5), round-trip min/avg/max = 1/2/4 ms"
        )
        self.assertEqual(result, (True, 20, 2.0))

    def test_keeps_latency_empty_when_not_reported(self):
        result = connectivityService.parse_cisco_ping_output(
            "Success rate is 100 percent (5/5)"
        )
        self.assertEqual(result, (True, 0, None))

    def test_rejects_unparseable_output(self):
        with self.assertRaises(ConnectivityResultParseException):
            connectivityService.parse_cisco_ping_output("unexpected device output")


class PingCatalogTests(unittest.TestCase):
    def test_ping_capability_supports_router_and_switch_only(self):
        ping = next(task for task in get_catalog() if task.id == "ping")
        self.assertEqual(ping.supported_device_types, ["router", "switch"])
        validate_automation_for_device("ping", "router")
        validate_automation_for_device("ping", "switch")
        with self.assertRaises(UnsupportedAutomationException):
            validate_automation_for_device("ping", "host")


class ConnectivityServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_router_ping_returns_normalized_response(self):
        destination = IPv4Address("10.0.0.2")
        with (
            patch.object(
                connectivityService,
                "get_node_device_type",
                new_callable=AsyncMock,
                return_value="router",
            ),
            patch.object(
                connectivityService,
                "get_node_console",
                new_callable=AsyncMock,
                return_value=("127.0.0.1", 5000),
            ),
            patch.object(
                connectivityService,
                "run_commands",
                new_callable=AsyncMock,
                return_value={
                    "ping 10.0.0.2": "Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms"
                },
            ) as run_commands,
        ):
            result = await connectivityService.run_node_ping(
                db=None,
                project_id=1,
                node_id="router-1",
                destination=destination,
                current_user=None,
            )

        self.assertEqual(
            result,
            {
                "source_node_id": "router-1",
                "destination": destination,
                "reachable": True,
                "packet_loss_percent": 0,
                "latency_ms": 2.0,
            },
        )
        self.assertEqual(run_commands.await_args.kwargs["commands"], ["ping 10.0.0.2"])
        self.assertEqual(run_commands.await_args.kwargs["timeout"], 30)

    async def test_switch_ping_is_supported(self):
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="switch"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock, return_value={"ping 10.0.0.2": "Success rate is 0 percent (0/5)"}),
        ):
            result = await connectivityService.run_node_ping(
                db=None,
                project_id=1,
                node_id="switch-1",
                destination=IPv4Address("10.0.0.2"),
                current_user=None,
            )

        self.assertFalse(result["reachable"])
        self.assertEqual(result["packet_loss_percent"], 100)

    async def test_host_is_rejected_before_console_or_netmiko(self):
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="host"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock) as run_commands,
        ):
            with self.assertRaises(UnsupportedAutomationException):
                await connectivityService.run_node_ping(
                    db=None,
                    project_id=1,
                    node_id="host-1",
                    destination=IPv4Address("10.0.0.2"),
                    current_user=None,
                )

        get_console.assert_not_awaited()
        run_commands.assert_not_awaited()

    async def test_unknown_device_is_rejected_before_console_or_netmiko(self):
        with (
            patch.object(
                connectivityService,
                "get_node_device_type",
                new_callable=AsyncMock,
                side_effect=DeviceTypeUndeterminedException(
                    "The device type could not be determined for this node."
                ),
            ),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock) as run_commands,
        ):
            with self.assertRaises(DeviceTypeUndeterminedException):
                await connectivityService.run_node_ping(
                    db=None,
                    project_id=1,
                    node_id="unknown-1",
                    destination=IPv4Address("10.0.0.2"),
                    current_user=None,
                )

        get_console.assert_not_awaited()
        run_commands.assert_not_awaited()

    async def test_supported_ping_orders_validation_before_console_and_netmiko(self):
        calls = []
        original_validate = connectivityService.validate_automation_for_device

        async def get_device_type(*args, **kwargs):
            calls.append("classification")
            return "router"

        def validate_ping(*args, **kwargs):
            calls.append("validation")
            return original_validate(*args, **kwargs)

        async def get_console(*args, **kwargs):
            calls.append("console")
            return "127.0.0.1", 5000

        async def run_ping_command(*args, **kwargs):
            calls.append("netmiko")
            return {"ping 10.0.0.2": "Success rate is 100 percent (5/5)"}

        with (
            patch.object(connectivityService, "get_node_device_type", side_effect=get_device_type),
            patch.object(connectivityService, "validate_automation_for_device", side_effect=validate_ping),
            patch.object(connectivityService, "get_node_console", side_effect=get_console),
            patch.object(connectivityService, "run_commands", side_effect=run_ping_command),
        ):
            await connectivityService.run_node_ping(
                db=None,
                project_id=1,
                node_id="router-1",
                destination=IPv4Address("10.0.0.2"),
                current_user=None,
            )

        self.assertEqual(calls, ["classification", "validation", "console", "netmiko"])

    async def test_netmiko_unreachable_is_preserved(self):
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, return_value="router"),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock, side_effect=NetmikoUnreachableException("console refused")),
        ):
            with self.assertRaises(NetmikoUnreachableException):
                await connectivityService.run_node_ping(
                    db=None,
                    project_id=1,
                    node_id="router-1",
                    destination=IPv4Address("10.0.0.2"),
                    current_user=None,
                )

    async def test_gns3_classification_outage_is_preserved(self):
        with (
            patch.object(connectivityService, "get_node_device_type", new_callable=AsyncMock, side_effect=GNS3UnreachableException("GNS3 server timed out")),
            patch.object(connectivityService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(connectivityService, "run_commands", new_callable=AsyncMock) as run_commands,
        ):
            with self.assertRaises(GNS3UnreachableException):
                await connectivityService.run_node_ping(
                    db=None,
                    project_id=1,
                    node_id="router-1",
                    destination=IPv4Address("10.0.0.2"),
                    current_user=None,
                )

        get_console.assert_not_awaited()
        run_commands.assert_not_awaited()


class ConnectivityApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_host_failure_returns_422(self):
        with patch.object(
            connectivityService,
            "run_node_ping",
            new_callable=AsyncMock,
            side_effect=UnsupportedAutomationException(
                "Automation 'ping' is not supported for device type 'host'."
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                await connectivity.ping_node(
                    project_id=1,
                    node_id="host-1",
                    payload=PingRequest(destination="10.0.0.2"),
                    db=None,
                    current_user=SimpleNamespace(),
                )

        self.assertEqual(raised.exception.status_code, 422)

    async def test_unknown_device_failure_returns_422(self):
        with patch.object(
            connectivityService,
            "run_node_ping",
            new_callable=AsyncMock,
            side_effect=DeviceTypeUndeterminedException(
                "The device type could not be determined for this node."
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                await connectivity.ping_node(
                    project_id=1,
                    node_id="unknown-1",
                    payload=PingRequest(destination="10.0.0.2"),
                    db=None,
                    current_user=SimpleNamespace(),
                )

        self.assertEqual(raised.exception.status_code, 422)


class ProjectConnectivityCheckTests(unittest.IsolatedAsyncioTestCase):
    def _node(self, node_id, name, interface_name, ip):
        return {
            "node_id": node_id,
            "name": name,
            "ports": [
                {
                    "adapter_number": 0,
                    "port_number": 0,
                    "name": interface_name,
                }
            ],
            "node_type": "dynamips",
        }

    def _discovered(self, node_id, name, interface_name, ip):
        return [
            connectivityService.DiscoveredInterface(
                node_id=node_id,
                node_name=name,
                interface=interface_name,
                ip_address=IPv4Address(ip) if ip else None,
                status="up",
                protocol="up",
            )
        ]

    async def test_project_check_runs_bidirectional_neighbor_pings(self):
        nodes = [
            self._node("r1", "R1", "FastEthernet0/0", "10.0.0.1"),
            self._node("r2", "R2", "FastEthernet0/0", "10.0.0.2"),
        ]
        links = [
            {
                "link_id": "l1",
                "nodes": [
                    {"node_id": "r1", "adapter_number": 0, "port_number": 0},
                    {"node_id": "r2", "adapter_number": 0, "port_number": 0},
                ],
            }
        ]

        async def discover(*args, **kwargs):
            node_id = kwargs["node_id"]
            node = next(item for item in nodes if item["node_id"] == node_id)
            return self._discovered(
                node_id,
                node["name"],
                node["ports"][0]["name"],
                "10.0.0.1" if node_id == "r1" else "10.0.0.2",
            )

        async def ping(*args, **kwargs):
            return {
                "source_node_id": kwargs["node_id"],
                "destination": kwargs["destination"],
                "reachable": True,
                "packet_loss_percent": 0,
                "latency_ms": 1.0,
            }

        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", side_effect=discover),
            patch.object(connectivityService, "get_project_links", new_callable=AsyncMock, return_value=links),
            patch.object(connectivityService, "run_node_ping", side_effect=ping) as run_ping,
        ):
            result = await connectivityService.check_project_connectivity(None, 1, None)

        self.assertEqual(len(result["results"]), 2)
        self.assertEqual([item.state for item in result["results"]], ["reachable", "reachable"])
        self.assertEqual(run_ping.await_count, 2)
        destinations = [call.kwargs["destination"] for call in run_ping.await_args_list]
        self.assertEqual(destinations, [IPv4Address("10.0.0.2"), IPv4Address("10.0.0.1")])

    async def test_ambiguous_port_mapping_is_skipped_without_ping(self):
        nodes = [
            self._node("r1", "R1", "FastEthernet0/0", "10.0.0.1"),
            {"node_id": "r2", "name": "R2", "node_type": "dynamips"},
        ]
        links = [
            {
                "link_id": "l1",
                "nodes": [
                    {"node_id": "r1", "adapter_number": 0, "port_number": 0},
                    {"node_id": "r2", "adapter_number": 0, "port_number": 0},
                ],
            }
        ]

        async def discover(*args, **kwargs):
            if kwargs["node_id"] == "r1":
                return self._discovered("r1", "R1", "FastEthernet0/0", "10.0.0.1")
            return self._discovered("r2", "R2", "FastEthernet0/0", "10.0.0.2")

        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", side_effect=discover),
            patch.object(connectivityService, "get_project_links", new_callable=AsyncMock, return_value=links),
            patch.object(connectivityService, "run_node_ping", new_callable=AsyncMock) as run_ping,
        ):
            result = await connectivityService.check_project_connectivity(None, 1, None)

        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(all(item.state == "skipped" for item in result["results"]))
        self.assertTrue(all(item.reason == "interface_mapping_ambiguous" for item in result["results"]))
        run_ping.assert_not_awaited()

    async def test_down_destination_is_skipped_without_ping(self):
        nodes = [
            self._node("r1", "R1", "FastEthernet0/0", "10.0.0.1"),
            self._node("r2", "R2", "FastEthernet0/0", "10.0.0.2"),
        ]
        links = [
            {
                "link_id": "l1",
                "nodes": [
                    {"node_id": "r1", "adapter_number": 0, "port_number": 0},
                    {"node_id": "r2", "adapter_number": 0, "port_number": 0},
                ],
            }
        ]

        async def discover(*args, **kwargs):
            node_id = kwargs["node_id"]
            name = "R1" if node_id == "r1" else "R2"
            item = connectivityService.DiscoveredInterface(
                node_id=node_id,
                node_name=name,
                interface="FastEthernet0/0",
                ip_address=IPv4Address("10.0.0.1" if node_id == "r1" else "10.0.0.2"),
                status="up" if node_id == "r1" else "down",
                protocol="up" if node_id == "r1" else "down",
            )
            return [item]

        with (
            patch.object(connectivityService, "get_project_nodes", new_callable=AsyncMock, return_value=nodes),
            patch.object(connectivityService, "discover_node_interfaces", side_effect=discover),
            patch.object(connectivityService, "get_project_links", new_callable=AsyncMock, return_value=links),
            patch.object(connectivityService, "run_node_ping", new_callable=AsyncMock) as run_ping,
        ):
            result = await connectivityService.check_project_connectivity(None, 1, None)

        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(all(item.state == "skipped" for item in result["results"]))
        self.assertIn("protocol_down", {item.reason for item in result["results"]})
        run_ping.assert_not_awaited()
