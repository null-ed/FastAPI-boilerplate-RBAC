import uuid as uuid_pkg
from datetime import UTC, datetime
from uuid6 import uuid7

from sqlalchemy import Boolean, DateTime, text
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column


class IDMixin:
    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7, server_default=text("gen_random_uuid()"), init=False
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(UTC), server_default=text("current_timestamp(0)"), init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, onupdate=datetime.now(UTC), server_default=text("current_timestamp(0)"), init=False
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, init=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, init=False)
