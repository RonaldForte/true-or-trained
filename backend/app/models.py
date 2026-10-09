"""Database tables. Alembic migrations in backend/migrations are generated from these models."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, MetaData, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # Predictable constraint names, so later migrations can alter or drop them by name.
    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "ix": "ix_%(table_name)s_%(column_0_name)s",
        }
    )


class Image(Base):
    """One image file on R2 (stored as {id}.webp) and who to credit for it."""

    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    credit_source: Mapped[str] = mapped_column(Text)
    license: Mapped[str] = mapped_column(Text)
    license_url: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)


class Pair(Base):
    """A real photo and its AI twin of the same subject: one round of the game."""

    __tablename__ = "pairs"
    __table_args__ = (
        CheckConstraint("real_image_id <> ai_image_id", name="real_and_ai_differ"),
        CheckConstraint("source IN ('dataset', 'user')", name="source_valid"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="status_valid"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    caption: Mapped[str] = mapped_column(Text)
    generator: Mapped[str] = mapped_column(Text)
    real_image_id: Mapped[str] = mapped_column(ForeignKey("images.id"), unique=True)
    ai_image_id: Mapped[str] = mapped_column(ForeignKey("images.id"), unique=True)
    source: Mapped[str] = mapped_column(String(16))
    # Defaults to pending so nothing reaches players until it is explicitly approved.
    status: Mapped[str] = mapped_column(String(16), server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
