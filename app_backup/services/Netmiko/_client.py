import asyncio
from typing import Any, Callable

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
    ConnectionException,
)

from app.core.exceptions import (
    NetmikoUnreachableException,
    NetmikoAuthException,
)


def _open_and_run_sync(
    device_params: dict[str, Any],
    work_fn: Callable[[Any], Any],
) -> Any:

    connection = ConnectHandler(**device_params)

    try:
        return work_fn(connection)
    finally:
        connection.disconnect()


########################## Run Session ##########################
async def run_session(
    host: str,
    port: int,
    work_fn: Callable[[Any], Any],
    device_type: str = "cisco_ios_telnet",
    username: str = "",
    password: str = "",
    secret: str = "",
    timeout: int = 10,
) -> Any:

    device_params = {
        "device_type": device_type,
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "secret": secret,
        "timeout": timeout,
        "fast_cli": False,
    }

    try:
        return await asyncio.to_thread(
            _open_and_run_sync,
            device_params,
            work_fn,
        )
    except NetmikoAuthenticationException as e:
        raise NetmikoAuthException(str(e))
    except (
        NetmikoTimeoutException,
        ConnectionException,
        ConnectionRefusedError,
        OSError,
    ) as e:
        raise NetmikoUnreachableException(str(e))
####################################################################