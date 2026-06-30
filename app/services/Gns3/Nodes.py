from typing import Any

from app.core.exceptions import GNS3RequestException
from app.services.Gns3._client import _call


########################## List Nodes ##########################
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
################################################################

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
################################################################

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
                "compute_id": payload.get("compute_id", "local"),
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
################################################################

########################## Start Node #########################
async def start_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "POST",
        f"/v2/projects/{project_id}/nodes/{node_id}/start",
    )
################################################################

########################## Stop Node ##########################
async def stop_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "POST",
        f"/v2/projects/{project_id}/nodes/{node_id}/stop",
    )
################################################################

########################## Reload Node ########################
async def reload_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "POST",
        f"/v2/projects/{project_id}/nodes/{node_id}/reload",
    )
################################################################

########################## Delete Node ########################
async def delete_node(
    project_id: str,
    node_id: str,
) -> None:

    await _call(
        "DELETE",
        f"/v2/projects/{project_id}/nodes/{node_id}",
    )
################################################################

########################## Rename Node ########################
async def rename_node(
    project_id: str,
    node_id: str,
    name: str,
) -> dict[str, Any]:

    result = await _call(
        "PUT",
        f"/v2/projects/{project_id}/nodes/{node_id}",
        json={"name": name},
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
################################################################

########################## Move Node ##########################
async def move_node(
    project_id: str,
    node_id: str,
    x: int,
    y: int,
) -> dict[str, Any]:

    result = await _call(
        "PUT",
        f"/v2/projects/{project_id}/nodes/{node_id}",
        json={"x": x, "y": y},
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
################################################################