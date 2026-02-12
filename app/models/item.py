import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ClothingSize(str, enum.Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"


class ItemCondition(str, enum.Enum):
    NEW_WITH_TAGS = "new_with_tags"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class ItemCategory(str, enum.Enum):
    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"
    SHOES = "shoes"
    ACCESSORIES = "accessories"
    OTHER = "other"


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    size: Mapped[ClothingSize] = mapped_column(Enum(ClothingSize, native_enum=False))
    condition: Mapped[ItemCondition] = mapped_column(
        Enum(ItemCondition, native_enum=False)
    )
    category: Mapped[ItemCategory] = mapped_column(
        Enum(ItemCategory, native_enum=False)
    )
    image_urls: Mapped[list[str]] = mapped_column(
        JSON, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
