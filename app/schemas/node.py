from pydantic import BaseModel, Field,ConfigDict,model_validator


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    template_id: str | None = None

    node_type: str | None = None

    compute_id: str = "local"



class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    node_id: str
    name: str
    node_type: str

    status: str | None = None

    console: int | None = None
    console_host: str | None = None

    compute_id: str | None = None

    x: int
    y: int



class NodeUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )


class NodeUpdatePosition(BaseModel):
    x: int
    y: int