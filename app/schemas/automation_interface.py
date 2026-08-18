from pydantic import BaseModel, Field


class InterfaceIpRequest(BaseModel):
    interface: str = Field(..., min_length=1)
    ip_address: str = Field(..., min_length=1)
    subnet_mask: str = Field(..., min_length=1)
    secret: str = ""


class InterfaceIpResponse(BaseModel):
    output: str
