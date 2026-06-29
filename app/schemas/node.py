from pydantic import BaseModel, Field


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    template_id: str | None = None

    node_type: str | None = None

    compute_id: str = "local"

    x: int = 0
    y: int = 0


class NodeResponse(BaseModel):
    node_id: str
    name: str
    node_type: str
    status: str | None
    console: int | None
    console_host: str | None
    x: int
    y: int
    compute_id: str | None

from pydantic import BaseModel, Field


class NodeUpadte(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )


class NodeUpdatePosition(BaseModel):
    x: int
    y: int