from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import ClothingSize, Item, ItemCategory, ItemCondition


async def create_item(db: AsyncSession, seller_id: int, **kwargs) -> Item:
    item = Item(seller_id=seller_id, **kwargs)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_item(db: AsyncSession, item_id: int) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


async def list_items(
    db: AsyncSession,
    category: ItemCategory | None = None,
    size: ClothingSize | None = None,
    condition: ItemCondition | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Item]:
    stmt = select(Item)
    if category:
        stmt = stmt.where(Item.category == category)
    if size:
        stmt = stmt.where(Item.size == size)
    if condition:
        stmt = stmt.where(Item.condition == condition)
    stmt = stmt.order_by(Item.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_item(db: AsyncSession, item: Item, **kwargs) -> Item:
    for key, value in kwargs.items():
        if value is not None:
            setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: Item) -> None:
    await db.delete(item)
    await db.commit()
