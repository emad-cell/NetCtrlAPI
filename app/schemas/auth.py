from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: UserRole  

    model_config = {"from_attributes": True}
