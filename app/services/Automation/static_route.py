def build_static_route_commands(
    destination: str,
    subnet_mask: str,
    next_hop: str,
) -> list[str]:

    return [
        f"ip route {destination} {subnet_mask} {next_hop}",
    ]
