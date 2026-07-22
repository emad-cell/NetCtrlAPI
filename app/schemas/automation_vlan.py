from pydantic import BaseModel, Field


class VlanCreateRequest(BaseModel):
    vlan_id: int = Field(..., ge=1, le=4094)
    name: str = Field(..., min_length=1)
    interface: str | None = None
    secret: str = ""


class VlanCreateResponse(BaseModel):
    output: str