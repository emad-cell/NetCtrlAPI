import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.api import automation
from app.core.exceptions import (
    DeviceTypeUndeterminedException,
    GNS3RequestException,
    GNS3UnreachableException,
    UnsupportedAutomationException,
)
from app.schemas.automation import CommandRequest
from app.schemas.automation_catalog import AutomationTask
from app.schemas.node import NodeResponse
from app.schemas.template import TemplateResponse
from app.services.Automation.catalog import validate_automation_for_device
from app.services import automationService
from app.services.deviceClassificationService import get_device_type, get_node_device_type


class SchemaTests(unittest.TestCase):
    def test_node_response_accepts_template_id(self):
        node = NodeResponse(
            node_id="node-1",
            name="R1",
            node_type="qemu",
            template_id="template-1",
            x=0,
            y=0,
        )
        self.assertEqual(node.template_id, "template-1")

    def test_template_response_accepts_device_type(self):
        template = TemplateResponse(
            template_id="template-1",
            name="Cisco IOSv",
            template_type="qemu",
            device_type="router",
        )
        self.assertEqual(template.device_type, "router")

    def test_catalog_includes_supported_device_types(self):
        task = AutomationTask(
            id="task",
            name="Task",
            description="Test task",
            category="Test",
            endpoint="/task",
            params=[],
            supported_device_types=["router"],
        )
        self.assertEqual(task.supported_device_types, ["router"])


class DeviceClassificationTests(unittest.IsolatedAsyncioTestCase):
    def test_router_classification(self):
        self.assertEqual(
            get_device_type({"template_id": "r1", "category": "Routers"}),
            "router",
        )

    def test_switch_classification(self):
        self.assertEqual(
            get_device_type({"template_id": "sw1", "category": "Switches"}),
            "switch",
        )

    def test_host_classification(self):
        self.assertEqual(
            get_device_type({"template_id": "pc1", "category": "End devices"}),
            "host",
        )

    def test_unknown_template_is_not_classified(self):
        self.assertIsNone(
            get_device_type({"template_id": "unknown", "name": "Custom appliance"})
        )

    async def test_node_without_template_id_is_rejected_as_undetermined(self):
        with (
            patch(
                "app.services.deviceClassificationService.get_project_by_id",
                return_value=SimpleNamespace(project_id="project-1"),
            ),
            patch(
                "app.services.deviceClassificationService.get_gns3_node",
                new_callable=AsyncMock,
                return_value={"node_id": "node-1"},
            ),
        ):
            with self.assertRaises(DeviceTypeUndeterminedException):
                await get_node_device_type(
                    db=None,
                    project_id=1,
                    node_id="node-1",
                    current_user=None,
                )

    async def test_deleted_template_is_rejected_without_leaking_gns3_detail(self):
        raw_gns3_detail = '{"message":"template database details"}'
        with (
            patch(
                "app.services.deviceClassificationService.get_project_by_id",
                return_value=SimpleNamespace(project_id="project-1"),
            ),
            patch(
                "app.services.deviceClassificationService.get_gns3_node",
                new_callable=AsyncMock,
                return_value={"node_id": "node-1", "template_id": "deleted-template"},
            ),
            patch(
                "app.services.deviceClassificationService.get_gns3_template",
                new_callable=AsyncMock,
                side_effect=GNS3RequestException(404, raw_gns3_detail),
            ),
        ):
            with self.assertRaisesRegex(
                DeviceTypeUndeterminedException,
                "device type could not be determined",
            ) as raised:
                await get_node_device_type(
                    db=None,
                    project_id=1,
                    node_id="node-1",
                    current_user=None,
                )

        self.assertNotIn(raw_gns3_detail, str(raised.exception))

    async def test_gns3_outage_remains_an_infrastructure_error(self):
        with (
            patch(
                "app.services.deviceClassificationService.get_project_by_id",
                return_value=SimpleNamespace(project_id="project-1"),
            ),
            patch(
                "app.services.deviceClassificationService.get_gns3_node",
                new_callable=AsyncMock,
                return_value={"node_id": "node-1", "template_id": "template-1"},
            ),
            patch(
                "app.services.deviceClassificationService.get_gns3_template",
                new_callable=AsyncMock,
                side_effect=GNS3UnreachableException("GNS3 server timed out"),
            ),
        ):
            with self.assertRaises(GNS3UnreachableException):
                await get_node_device_type(
                    db=None,
                    project_id=1,
                    node_id="node-1",
                    current_user=None,
                )


class AutomationCapabilityTests(unittest.TestCase):
    def test_router_interface_ip_is_allowed(self):
        validate_automation_for_device("interface_ip", "router")

    def test_switch_vlan_is_allowed(self):
        validate_automation_for_device("create_vlan", "switch")

    def test_router_vlan_is_rejected(self):
        with self.assertRaisesRegex(UnsupportedAutomationException, "create_vlan"):
            validate_automation_for_device("create_vlan", "router")

    def test_switch_interface_ip_is_rejected(self):
        with self.assertRaisesRegex(UnsupportedAutomationException, "interface_ip"):
            validate_automation_for_device("interface_ip", "switch")

    def test_host_configure_is_rejected(self):
        with self.assertRaisesRegex(UnsupportedAutomationException, "run_configure"):
            validate_automation_for_device("run_configure", "host")

    def test_generic_show_command_is_rejected_for_host(self):
        with self.assertRaisesRegex(UnsupportedAutomationException, "run_command"):
            validate_automation_for_device("run_command", "host")


class ExistingAutomationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_unsupported_automation_stops_before_console_or_netmiko(self):
        calls = []

        async def get_device_type(*args, **kwargs):
            calls.append("classification")
            return "router"

        with (
            patch.object(automationService, "get_node_device_type", side_effect=get_device_type),
            patch.object(automationService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(automationService, "run_config", new_callable=AsyncMock) as run_config,
        ):
            with self.assertRaises(UnsupportedAutomationException):
                await automationService.run_node_vlan(
                    db=None,
                    project_id=1,
                    node_id="node-1",
                    vlan_id=10,
                    name="SALES",
                    current_user=None,
                )

        self.assertEqual(calls, ["classification"])
        get_console.assert_not_awaited()
        run_config.assert_not_awaited()

    async def test_unknown_device_stops_before_console_or_netmiko(self):
        with (
            patch.object(
                automationService,
                "get_node_device_type",
                new_callable=AsyncMock,
                side_effect=DeviceTypeUndeterminedException(
                    "The device type could not be determined for this node."
                ),
            ),
            patch.object(automationService, "get_node_console", new_callable=AsyncMock) as get_console,
            patch.object(automationService, "run_config", new_callable=AsyncMock) as run_config,
        ):
            with self.assertRaises(DeviceTypeUndeterminedException):
                await automationService.run_node_vlan(
                    db=None,
                    project_id=1,
                    node_id="node-1",
                    vlan_id=10,
                    name="SALES",
                    current_user=None,
                )

        get_console.assert_not_awaited()
        run_config.assert_not_awaited()

    async def test_supported_automation_reaches_console_then_netmiko(self):
        calls = []

        async def get_device_type(*args, **kwargs):
            calls.append("classification")
            return "switch"

        async def get_console(*args, **kwargs):
            calls.append("console")
            return "127.0.0.1", 5000

        async def run_config(*args, **kwargs):
            calls.append("netmiko")
            return "ok"

        with (
            patch.object(automationService, "get_node_device_type", side_effect=get_device_type),
            patch.object(automationService, "get_node_console", side_effect=get_console),
            patch.object(automationService, "run_config", side_effect=run_config),
        ):
            result = await automationService.run_node_vlan(
                db=None,
                project_id=1,
                node_id="node-1",
                vlan_id=10,
                name="SALES",
                current_user=None,
            )

        self.assertEqual(result, "ok")
        self.assertEqual(calls, ["classification", "console", "netmiko"])

    async def test_generic_command_automation_still_runs_after_validation(self):
        with (
            patch.object(automationService, "_validate_node_automation", new_callable=AsyncMock),
            patch.object(automationService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(automationService, "run_commands", new_callable=AsyncMock, return_value={"show ip int brief": "ok"}) as run_commands,
        ):
            result = await automationService.run_node_commands(
                db=None,
                project_id=1,
                node_id="node-1",
                commands=["show ip int brief"],
                current_user=None,
            )

        self.assertEqual(result, {"show ip int brief": "ok"})
        run_commands.assert_awaited_once()

    async def test_vlan_automation_still_builds_and_runs_commands(self):
        with (
            patch.object(automationService, "_validate_node_automation", new_callable=AsyncMock),
            patch.object(automationService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(automationService, "run_config", new_callable=AsyncMock, return_value="ok") as run_config,
        ):
            result = await automationService.run_node_vlan(
                db=None,
                project_id=1,
                node_id="node-1",
                vlan_id=10,
                name="SALES",
                interface="Ethernet0/1",
                current_user=None,
            )

        self.assertEqual(result, "ok")
        self.assertEqual(
            run_config.await_args.kwargs["commands"],
            ["vlan 10", "name SALES", "exit", "interface Ethernet0/1", "switchport mode access", "switchport access vlan 10", "exit"],
        )

    async def test_interface_ip_automation_still_builds_and_runs_commands(self):
        with (
            patch.object(automationService, "_validate_node_automation", new_callable=AsyncMock),
            patch.object(automationService, "get_node_console", new_callable=AsyncMock, return_value=("127.0.0.1", 5000)),
            patch.object(automationService, "run_config", new_callable=AsyncMock, return_value="ok") as run_config,
        ):
            result = await automationService.run_node_interface_ip(
                db=None,
                project_id=1,
                node_id="node-1",
                interface="GigabitEthernet0/0",
                ip_address="10.0.0.1",
                subnet_mask="255.255.255.0",
                current_user=None,
            )

        self.assertEqual(result, "ok")
        self.assertEqual(
            run_config.await_args.kwargs["commands"],
            ["interface GigabitEthernet0/0", "ip address 10.0.0.1 255.255.255.0", "no shutdown"],
        )


class AutomationApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_classification_failure_returns_controlled_422(self):
        raw_gns3_detail = '{"message":"template database details"}'
        with patch.object(
            automationService,
            "run_node_commands",
            new_callable=AsyncMock,
            side_effect=DeviceTypeUndeterminedException(
                "The device type could not be determined for this node."
            )
        ):
            with self.assertRaises(HTTPException) as raised:
                await automation.run_commands(
                    project_id=1,
                    node_id="node-1",
                    payload=CommandRequest(commands=["show version"]),
                    db=None,
                    current_user=SimpleNamespace(),
                )

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(
            raised.exception.detail,
            "The device type could not be determined for this node.",
        )
        self.assertNotIn(raw_gns3_detail, raised.exception.detail)
