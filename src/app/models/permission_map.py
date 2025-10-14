from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class PermissionMap(Base):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint("permission_name", "user_id", name="uq_permission_user"),
        UniqueConstraint("permission_name", "role_id", name="uq_permission_role"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)

    permission_name: Mapped[str] = mapped_column(String(100), index=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), index=True, default=None)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("role.id"), index=True, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)