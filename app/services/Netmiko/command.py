from functools import partial
from typing import Any

from app.services.Netmiko._client import run_session


def _read_commands(
    connection: Any,
    commands: list[str],
) -> dict[str, str]:

    return {
        command: connection.send_command(command)
        for command in commands
    }


########################## Run Commands ##########################
async def run_commands(
    host: str,
    port: int,
    commands: list[str],
    device_type: str = "cisco_ios_telnet",
    username: str = "",
    password: str = "",
    secret: str = "",
    timeout: int = 10,
) -> dict[str, str]:

    return await run_session(
        host=host,
        port=port,
        work_fn=partial(_read_commands, commands=commands),
        device_type=device_type,
        username=username,
        password=password,
        secret=secret,
        timeout=timeout,
    )
####################################################################