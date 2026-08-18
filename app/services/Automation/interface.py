def build_interface_ip_commands(
    interface: str,
    ip_address: str,
    subnet_mask: str,
) -> list[str]:

    return [
        f"interface {interface}",
        f"ip address {ip_address} {subnet_mask}",
        "no shutdown",
    ]
