from typing import Any

from app.core.exceptions import GNS3RequestException
from app.services.Gns3._client import _call


########################## List Links ##########################
async def get_links(
    project_id: str,
) -> list[dict[str, Any]]:

    result = await _call(
        "GET",
        f"/v2/projects/{project_id}/links",
    )

    if isinstance(result, list):
        return result

    raise GNS3RequestException(
        status_code=500,
        detail="Unexpected response from GNS3.",
    )
################################################################

########################## Get Link ###########################
async def get_link(
    project_id: str,
    link_id: str,
) -> dict[str, Any]:

    result = await _call(
        "GET",
        f"/v2/projects/{project_id}/links/{link_id}",
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
################################################################

########################## Create Link ########################
async def create_link(
    project_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:

    result = await _call(
        "POST",
        f"/v2/projects/{project_id}/links",
        json=payload,
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
################################################################

########################## Delete Link ########################
async def delete_link(
    project_id: str,
    link_id: str,
) -> None:

    await _call(
        "DELETE",
        f"/v2/projects/{project_id}/links/{link_id}",
    )
################################################################