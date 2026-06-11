import asyncio
import signal
import logging
from asyncio.subprocess import Process

logger = logging.getLogger(__name__)

_process: Process | None = None


async def start_gns3_server() -> None:
    global _process

    if _process and _process.returncode is None:
        logger.info("GNS3 server already running (PID %s)", _process.pid)
        return

    logger.info("Starting GNS3 server...")

    _process = await asyncio.create_subprocess_exec(
        "gns3server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    # Wait until GNS3 signals it's ready
    assert _process.stdout is not None
    async for line in _process.stdout:
        decoded = line.decode().strip()
        logger.debug("[gns3] %s", decoded)
        if "GNS3 server started" in decoded or "Uvicorn running" in decoded:
            break

    logger.info("GNS3 server ready (PID %s)", _process.pid)


async def stop_gns3_server() -> None:
    global _process

    if not _process or _process.returncode is not None:
        logger.info("GNS3 server is not running")
        return

    logger.info("Stopping GNS3 server (PID %s)...", _process.pid)

    _process.send_signal(signal.SIGTERM)

    try:
        await asyncio.wait_for(_process.wait(), timeout=10.0)
        logger.info("GNS3 server stopped cleanly")
    except asyncio.TimeoutError:
        logger.warning("GNS3 did not stop in time — sending SIGKILL")
        _process.kill()
        await _process.wait()

    _process = None


def get_server_status() -> dict:
    if _process is None:
        return {"running": False, "pid": None}
    if _process.returncode is not None:
        return {"running": False, "pid": None}
    return {"running": True, "pid": _process.pid}