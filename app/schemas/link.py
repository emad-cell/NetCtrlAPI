from pydantic import BaseModel, ConfigDict, Field


class LinkEndpoint(BaseModel):
    node_id: str = Field(..., min_length=1)
    adapter: int = Field(..., ge=0)
    port: int = Field(..., ge=0)


class LinkCreate(BaseModel):
    source: LinkEndpoint
    target: LinkEndpoint


class LinkNode(BaseModel):
    node_id: str
    adapter_number: int
    port_number: int


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    link_id: str
    nodes: list[LinkNode]