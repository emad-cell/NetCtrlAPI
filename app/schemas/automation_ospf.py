from pydantic import BaseModel, Field


class OspfCreateRequest(BaseModel):
    process_id: int = Field(..., ge=1)
    network: str = Field(..., min_length=1)
    wildcard: str = Field(..., min_length=1)
    area: int = Field(..., ge=0)
    secret: str = ""


class OspfCreateResponse(BaseModel):
    output: str
