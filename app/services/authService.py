from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.schemas.auth import RegisterRequest, TokenResponse, UserOut
from app.models.user import User 
from app.core.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)

def register_user(
    db: Session,
    payload: RegisterRequest
) -> User:

    existing_user = (
        db.query(User)
        .filter(User.username == payload.username)
        .first()
    )

    if existing_user:
        raise UserAlreadyExistsException("Username already taken")

    existing_email = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if existing_email:
        raise UserAlreadyExistsException("Email already registered")

    user = User(
        username=payload.username,
        email=payload.email.lower(),
        hashed_password=hash_password(
            payload.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

############################Login
def login_user(
    db: Session,
    identifier: str,  # Can be username or email
    password: str
) -> dict:

    user = (
        db.query(User)
        .filter(
            or_(
                User.email == identifier.lower(),
                User.username == identifier
            )
        )
        .first()
    )

    if not user:
        # Mitigate timing attack by performing a dummy hash verification
        hash_password(password)
        raise InvalidCredentialsException("Invalid credentials")
    if not verify_password(
        password,
        user.hashed_password
    ):
        raise InvalidCredentialsException("Invalid credentials")

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }