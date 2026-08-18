def build_ospf_commands(
    process_id: int,
    network: str,
    wildcard: str,
    area: int,
) -> list[str]:

    return [
        f"router ospf {process_id}",
        f"network {network} {wildcard} area {area}",
        "exit",
    ]
