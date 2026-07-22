from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    commands: list[str] = Field(..., min_length=1)
    secret: str = ""


class CommandResponse(BaseModel):
    results: dict[str, str]


class ConfigureRequest(BaseModel):
    commands: list[str] = Field(..., min_length=1)
    secret: str = ""


class ConfigureResponse(BaseModel):
    output: str