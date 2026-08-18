from pydantic import BaseModel, Field


class StaticRouteCreateRequest(BaseModel):
    destination: str = Field(..., min_length=1)
    subnet_mask: str = Field(..., min_length=1)
    next_hop: str = Field(..., min_length=1)
    secret: str = ""


class StaticRouteCreateResponse(BaseModel):
    output: str
