from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    project_id: str
    owner_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }