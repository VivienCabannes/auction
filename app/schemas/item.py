from datetime import datetime

from pydantic import BaseModel

from app.models.item import ClothingSize, ItemCategory, ItemCondition


class ItemCreate(BaseModel):
    title: str
    description: str
    size: ClothingSize
    condition: ItemCondition
    category: ItemCategory
    image_urls: list[str] = []


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    size: ClothingSize | None = None
    condition: ItemCondition | None = None
    category: ItemCategory | None = None
    image_urls: list[str] | None = None


class ItemResponse(BaseModel):
    id: int
    seller_id: int
    title: str
    description: str
    size: ClothingSize
    condition: ItemCondition
    category: ItemCategory
    image_urls: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
