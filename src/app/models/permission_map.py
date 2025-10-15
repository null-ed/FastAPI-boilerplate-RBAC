from datetime import UTC, datetime
import uuid as uuid_pkg

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base
from ..core.db.models import IDMixin, TimestampMixin



class PermissionMap(Base, IDMixin, TimestampMixin):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint("permission_name", "user_id", name="uq_permission_user"),
        UniqueConstraint("permission_name", "role_id", name="uq_permission_role"),
    )


    permission_name: Mapped[str] = mapped_column(String(100), index=True)

    user_id: Mapped[uuid_pkg.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), index=True, default=None)
    role_id: Mapped[uuid_pkg.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("role.id"), index=True, default=None)
