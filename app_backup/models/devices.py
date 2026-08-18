import enum

from sqlalchemy import Column, Enum, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime ,timezone
from app.db.database import Base
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)           # e.g. "R1", "Core-Switch"
    host = Column(String, nullable=False)           # IP address
    port = Column(Integer, default=22)
    device_type = Column(String, default="cisco_ios")  # Netmiko device type
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)       # encrypted at rest
    secret = Column(String, nullable=True)          # encrypted at rest when provided
    owner_id = Column(Integer, ForeignKey("users.id"),index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="devices")
