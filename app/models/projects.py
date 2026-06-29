from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"


    id: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String, nullable=False)

    project_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    owner = relationship("User", back_populates="projects")