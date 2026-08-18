from pydantic import BaseModel


class AutomationParam(BaseModel):
    name: str
    label: str
    type: str  # "string" | "int"
    required: bool = True
    placeholder: str | None = None


class AutomationTask(BaseModel):
    id: str
    name: str
    description: str
    category: str
    endpoint: str
    method: str = "POST"
    params: list[AutomationParam]
    supported_device_types: list[str]
