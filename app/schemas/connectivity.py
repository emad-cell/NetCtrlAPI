from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel


class PingRequest(BaseModel):
    destination: IPv4Address


class PingResponse(BaseModel):
    source_node_id: str
    destination: IPv4Address
    reachable: bool
    packet_loss_percent: int | None = None
    latency_ms: float | None = None


class DiscoveredInterface(BaseModel):
    node_id: str
    node_name: str
    interface: str
    ip_address: IPv4Address | None
    status: str
    protocol: str


class ConnectivityDiscoveryNodeResult(BaseModel):
    node_id: str
    node_name: str
    state: Literal["discovered", "skipped", "error"]
    reason: str | None = None


class ConnectivityEndpointsResponse(BaseModel):
    endpoints: list[DiscoveredInterface]
    node_results: list[ConnectivityDiscoveryNodeResult]


class ConnectivityCheckResult(BaseModel):
    source_node_id: str
    source_interface: str | None = None
    destination_node_id: str | None = None
    destination_interface: str | None = None
    destination_ip: IPv4Address | None = None
    state: Literal["reachable", "unreachable", "skipped", "error"]
    reason: str | None = None
    packet_loss_percent: int | None = None
    latency_ms: float | None = None


class ConnectivityCheckResponse(BaseModel):
    results: list[ConnectivityCheckResult]
