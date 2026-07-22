from functools import partial
from typing import Any

from app.services.Netmiko._client import run_session


def _apply_config(
    connection: Any,
    commands: list[str],
) -> str:

    if not connection.check_enable_mode():
        connection.enable()

    return connection.send_config_set(commands)


########################## Run Config ##########################
async def run_config(
    host: str,
    port: int,
    commands: list[str],
    device_type: str = "cisco_ios_telnet",
    username: str = "",
    password: str = "",
    secret: str = "",
    timeout: int = 10,
) -> str:

    return await run_session(
        host=host,
        port=port,
        work_fn=partial(_apply_config, commands=commands),
        device_type=device_type,
        username=username,
        password=password,
        secret=secret,
        timeout=timeout,
    )
##################################################################