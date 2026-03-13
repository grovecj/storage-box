from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    box_items: Mapped[list["BoxItem"]] = relationship(
        "BoxItem", back_populates="item"
    )


class BoxItem(Base):
    __tablename__ = "box_items"
    __table_args__ = (UniqueConstraint("box_id", "item_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    box_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("storage_boxes.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    box: Mapped["StorageBox"] = relationship("StorageBox", back_populates="box_items")
    item: Mapped["Item"] = relationship("Item", back_populates="box_items")
    tags: Mapped[list["BoxItemTag"]] = relationship(
        "BoxItemTag", back_populates="box_item", cascade="all, delete-orphan"
    )


class BoxItemTag(Base):
    __tablename__ = "box_item_tags"

    box_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("box_items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id"), primary_key=True
    )

    box_item: Mapped["BoxItem"] = relationship("BoxItem", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag")
