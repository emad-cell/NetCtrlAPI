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


########################## List Nodes #########################
async def get_nodes(
    project_id: str,
) -> list[dict[str, Any]]:

    result = await _call(
        "GET",
        f"/v2/projects/{project_id}/nodes",
    )

    if isinstance(result, list):
        return result

    return []
##########################

########################## Get Node ###########################
async def get_node(
    project_id: str,
    node_id: str,
) -> dict[str, Any]:

    result = await _call(
        "GET",
        f"/v2/projects/{project_id}/nodes/{node_id}",
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
##########################

########################## Create Node ########################
async def create_node(
    project_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:

    template_id = payload.get("template_id")

    if template_id:

        result = await _call(
            "POST",
            f"/v2/projects/{project_id}/templates/{template_id}",
            json={
                "x": payload.get("x", 0),
                "y": payload.get("y", 0),
                "compute_id": payload.get(
                    "compute_id",
                    "local",
                ),
            },
        )

    else:

        result = await _call(
            "POST",
            f"/v2/projects/{project_id}/nodes",
            json=payload,
        )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
##########################

########################## start and stop #####################
async def start_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "POST",
        f"/v2/projects/{project_id}/nodes/{node_id}/start",
        
    )
async def stop_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "POST",
        f"/v2/projects/{project_id}/nodes/{node_id}/stop",
    )
##########################

########################## Reload #############################
async def reload_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "POST",
        f"/v2/projects/{project_id}/nodes/{node_id}/reload",
    )
##########################

########################## Delete #############################
async def delete_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "DELETE",
        f"/v2/projects/{project_id}/nodes/{node_id}",
    )
##########################

########################## Rename #############################
async def rename_node(
    project_id: str,
    node_id: str,
    name: str,
) -> dict[str, Any]:

    result = await _call(
        "PUT",
        f"/v2/projects/{project_id}/nodes/{node_id}",
        json={
            "name": name,
        },
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
##########################

########################## Move ###############################
async def move_node(
    project_id: str,
    node_id: str,
    x: int,
    y: int,
) -> dict[str, Any]:

    result = await _call(
        "PUT",
        f"/v2/projects/{project_id}/nodes/{node_id}",
        json={
            "x": x,
            "y": y,
        },
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
##########################
