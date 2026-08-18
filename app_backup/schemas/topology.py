from pydantic import BaseModel

from app.schemas.project import ProjectResponse
from app.schemas.node import NodeResponse
from app.schemas.link import LinkResponse


class TopologyResponse(BaseModel):
    project: ProjectResponse
    nodes: list[NodeResponse]
    links: list[LinkResponse]