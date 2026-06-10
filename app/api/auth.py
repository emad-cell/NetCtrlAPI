from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, TokenResponse, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from pydantic import BaseModel
from app.services import authService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])



###################Register
@router.post(
    "/register",
    response_model=UserOut,
    status_code=201
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    try:
        return authService.register_user(db, payload)
    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
###################

###################Login
@router.post(
    "/login",
    response_model=TokenResponse
)
def login(

    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        return authService.login_user(
            db,
            form_data.username,  # this field name is 'username' in OAuth2 form, but can hold email
            form_data.password
        )
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
###################
   
###################current user
@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
###################