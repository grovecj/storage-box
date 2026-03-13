from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Integer, Sequence, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

box_code_seq = Sequence("box_code_seq", start=1)


class StorageBox(Base):
    __tablename__ = "storage_boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    box_code: Mapped[str] = mapped_column(
        String(8), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    box_items: Mapped[list["BoxItem"]] = relationship(
        "BoxItem", back_populates="box", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="box"
    )
