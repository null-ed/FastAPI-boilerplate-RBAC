from datetime import UTC, datetime
import uuid as uuid_pkg

from sqlalchemy import DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from ..core.db.models import IDMixin, TimestampMixin, SoftDeleteMixin


class User(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "user"
    
    name: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    phone_number: Mapped[str | None] = mapped_column(String(32), default=None)

    is_superuser: Mapped[bool] = mapped_column(default=False)

    tier_id: Mapped[uuid_pkg.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tier.id"), index=True, default=None, init=False)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_role",
        lazy="selectin",
        init=False,
    )