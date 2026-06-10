from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.models.user import UserRole,User
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db

# Define OAuth2 scheme indicating where to fetch the token from
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise credentials_exception

    return user

def require_role(allowed_roles: list[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        
        # Perform role check
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
