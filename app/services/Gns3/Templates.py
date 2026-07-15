from typing import Any

from app.core.exceptions import GNS3RequestException
from app.services.Gns3._client import _call


########################## List Templates ##########################
async def get_templates() -> list[dict[str, Any]]:

    result = await _call(
        "GET",
        "/v2/templates",
    )

    if isinstance(result, list):
        return result

    raise GNS3RequestException(
        status_code=500,
        detail="Unexpected response from GNS3.",
    )
######################################################################

########################## Get Template #############################
async def get_template(
    template_id: str,
) -> dict[str, Any]:

    result = await _call(
        "GET",
        f"/v2/templates/{template_id}",
    )

    if not isinstance(result, dict):
        raise GNS3RequestException(
            status_code=500,
            detail="Invalid response returned by GNS3.",
        )

    return result
######################################################################