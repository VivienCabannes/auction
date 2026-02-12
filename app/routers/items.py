from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.exceptions import bad_request, forbidden, not_found
from app.models.auction import AuctionStatus
from app.models.item import ClothingSize, ItemCategory, ItemCondition
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services import item as item_service
from app.services.auction import get_active_auction_for_item

router = APIRouter(prefix="/api/v1/items", tags=["items"])


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    data: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await item_service.create_item(
        db,
        seller_id=current_user.id,
        title=data.title,
        description=data.description,
        size=data.size,
        condition=data.condition,
        category=data.category,
        image_urls=data.image_urls,
    )
    return item


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    category: ItemCategory | None = Query(None),
    size: ClothingSize | None = Query(None),
    condition: ItemCondition | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items = await item_service.list_items(
        db, category=category, size=size, condition=condition, skip=skip, limit=limit
    )
    return items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await item_service.get_item(db, item_id)
    if item is None:
        raise not_found("Item not found")
    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await item_service.get_item(db, item_id)
    if item is None:
        raise not_found("Item not found")
    if item.seller_id != current_user.id:
        raise forbidden("Not your item")
    updated = await item_service.update_item(
        db,
        item,
        **data.model_dump(exclude_unset=True),
    )
    return updated


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await item_service.get_item(db, item_id)
    if item is None:
        raise not_found("Item not found")
    if item.seller_id != current_user.id:
        raise forbidden("Not your item")
    active_auction = await get_active_auction_for_item(db, item_id)
    if active_auction:
        raise bad_request("Cannot delete item with active auction")
    await item_service.delete_item(db, item)
