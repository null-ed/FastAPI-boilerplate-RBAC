from datetime import UTC, datetime
import uuid as uuid_pkg

from sqlalchemy import Boolean, DateTime, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from ..core.db.models import IDMixin, TimestampMixin



class Role(Base, IDMixin, TimestampMixin):
    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    permission_maps: Mapped[list["PermissionMap"]] = relationship(
        "PermissionMap",
        lazy="selectin",
        init=False,
    )
    
