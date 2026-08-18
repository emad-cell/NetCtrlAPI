import httpx
from app.core.config import settings
from app.core.exceptions import GNS3UnreachableException, GNS3RequestException


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=f"http://{settings.GNS3_HOST}:{settings.GNS3_PORT}",
        auth=(settings.GNS3_USER, settings.GNS3_PASS),
        timeout=10.0
    )

async def _call(method: str, path: str, **kwargs) -> dict | None:
    try:
        async with _client() as client:
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
    except httpx.ConnectError:
        raise GNS3UnreachableException("GNS3 server is unreachable")
    except httpx.TimeoutException:
        raise GNS3UnreachableException("GNS3 server timed out")
    except httpx.HTTPStatusError as e:
        raise GNS3RequestException(
            status_code=e.response.status_code,
            detail=e.response.text
        )
    

##########################Create Project
async def create_gns3_project(name: str) -> dict:
    result = await _call("POST", "/v2/projects", json={"name": name})
    assert result is not None, "GNS3 returned empty response on project create"
    return result
##########################

##########################Open Project
async def open_gns3_project(project_id: str) -> dict:
    result = await _call("POST", f"/v2/projects/{project_id}/open")
    assert result is not None, "GNS3 returned empty response on project open"
    return result

##########################

##########################Close Project
async def close_gns3_project(project_id: str) -> None:
    await _call("POST", f"/v2/projects/{project_id}/close")

##########################

##########################Delete Project
async def delete_gns3_project(project_id: str) -> None:
    await _call("DELETE", f"/v2/projects/{project_id}")
##########################