from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    permission_maps: Mapped[list["PermissionMap"]] = relationship(
        "PermissionMap",
        lazy="selectin",
        init=False,
    )
    
