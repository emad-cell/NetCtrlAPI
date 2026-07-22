def build_vlan_commands(
    vlan_id: int,
    name: str,
    interface: str | None = None,
) -> list[str]:

    commands = [
        f"vlan {vlan_id}",
        f"name {name}",
        "exit",
    ]

    if interface:
        commands += [
            f"interface {interface}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "exit",
        ]

    return commands