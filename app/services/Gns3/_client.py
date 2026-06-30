from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    GNS3RequestException,
    GNS3UnreachableException,
)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=f"http://{settings.GNS3_HOST}:{settings.GNS3_PORT}",
        auth=(
            settings.GNS3_USER,
            settings.GNS3_PASS,
        ),
        timeout=10.0,
    )


async def _call(
    method: str,
    path: str,
    **kwargs,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    try:
        async with _client() as client:
            response = await client.request(
                method,
                path,
                **kwargs,
            )
            response.raise_for_status()
            if not response.content:
                return None
            return response.json()

    except httpx.ConnectError:
        raise GNS3UnreachableException(
            "GNS3 server is unreachable"
        )
    except httpx.TimeoutException:
        raise GNS3UnreachableException(
            "GNS3 server timed out"
        )
    except httpx.HTTPStatusError as e:
        raise GNS3RequestException(
            status_code=e.response.status_code,
            detail=e.response.text,
        )