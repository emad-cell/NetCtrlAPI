import enum

from sqlalchemy import Column, Enum, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime ,timezone
from app.db.database import Base

class UserRole(str, enum.Enum):
    admin    = "admin"
    operator = "operator"
    viewer   = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role= Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One user can manage many devices
    devices = relationship("Device", back_populates="owner")
    projects = relationship(
    "Project",
    back_populates="owner"
)