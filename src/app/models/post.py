import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base
from ..core.db.models import IDMixin, TimestampMixin, SoftDeleteMixin



class Post(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "post"

    created_by_user_id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(String(63206))
    media_url: Mapped[str | None] = mapped_column(String, default=None)

