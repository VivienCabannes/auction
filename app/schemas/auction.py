from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.auction import AuctionStatus


class AuctionCreate(BaseModel):
    item_id: int
    start_price: Decimal
    start_time: datetime
    end_time: datetime


class AuctionResponse(BaseModel):
    id: int
    item_id: int
    seller_id: int
    start_price: Decimal
    current_highest_bid: Decimal | None
    start_time: datetime
    end_time: datetime
    original_end_time: datetime
    status: AuctionStatus
    winner_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
