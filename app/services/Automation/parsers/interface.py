import re
from ipaddress import IPv4Address

from app.core.exceptions import InterfaceDiscoveryParseException


HEADER_PATTERN = re.compile(r"^Interface\s+IP-Address\s+OK\?\s+Method\s+Status\s+Protocol$", re.IGNORECASE)
ROW_PATTERN = re.compile(
    r"^(?P<interface>\S+)\s+"
    r"(?P<ip_address>\S+)\s+"
    r"(?P<ok>YES|NO)\s+"
    r"(?P<method>\S+)\s+"
    r"(?P<status>administratively\s+down|up|down)\s+"
    r"(?P<protocol>up|down)$",
    re.IGNORECASE,
)


def parse_cisco_interface_brief(output: str) -> list[dict]:
    """Parse Cisco IOS ``show ip interface brief`` output without guessing rows."""
    rows: list[dict] = []
    header_found = False

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if not header_found:
            if HEADER_PATTERN.fullmatch(line):
                header_found = True
            continue

        match = ROW_PATTERN.fullmatch(line)
        if not match:
            raise InterfaceDiscoveryParseException(
                "The device interface state could not be determined."
            )

        ip_value = match.group("ip_address")
        try:
            ip_address = None if ip_value.lower() == "unassigned" else IPv4Address(ip_value)
        except ValueError as exc:
            raise InterfaceDiscoveryParseException(
                "The device interface state could not be determined."
            ) from exc

        rows.append(
            {
                "interface": match.group("interface"),
                "ip_address": ip_address,
                "status": " ".join(match.group("status").lower().split()),
                "protocol": match.group("protocol").lower(),
            }
        )

    if not header_found or not rows:
        raise InterfaceDiscoveryParseException(
            "The device interface state could not be determined."
        )

    return rows
