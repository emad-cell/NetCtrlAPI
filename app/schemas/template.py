from pydantic import BaseModel, ConfigDict


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template_id: str
    name: str
    category: str | None = None
    template_type: str
    compute_id: str | None = None
    symbol: str | None = None