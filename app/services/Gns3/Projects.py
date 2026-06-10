import httpx

from app.core.config import settings

##########################Create Project
async def create_gns3_project(name: str) -> dict:

    url = (
        f"http://{settings.GNS3_HOST}:"
        f"{settings.GNS3_PORT}/v2/projects"
    )

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url,
            json={"name": name},
            auth=(
                settings.GNS3_USER,
                settings.GNS3_PASS
            )
        )

    response.raise_for_status()

    return response.json()
##########################

##########################Open Project
async def open_gns3_project(
    project_id: str
) -> dict:

    url = (
        f"http://{settings.GNS3_HOST}:"
        f"{settings.GNS3_PORT}"
        f"/v2/projects/{project_id}/open"
    )

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url,
            auth=(
                settings.GNS3_USER,
                settings.GNS3_PASS
            )
        )

    response.raise_for_status()

    return response.json()
##########################

##########################Close Project
async def close_gns3_project(
    project_id: str
) -> None:

    url = (
        f"http://{settings.GNS3_HOST}:"
        f"{settings.GNS3_PORT}"
        f"/v2/projects/{project_id}/close"
    )

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url,
            auth=(
                settings.GNS3_USER,
                settings.GNS3_PASS
            )
        )

    response.raise_for_status()

##########################

##########################Delete Project
async def delete_gns3_project(
    project_id: str
) -> None:

    url = (
        f"http://{settings.GNS3_HOST}:"
        f"{settings.GNS3_PORT}"
        f"/v2/projects/{project_id}"
    )

    async with httpx.AsyncClient() as client:

        response = await client.delete(
            url,
            auth=(
                settings.GNS3_USER,
                settings.GNS3_PASS
            )
        )

    response.raise_for_status()
##########################