from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BidCreate(BaseModel):
    amount: Decimal


class BidResponse(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class BidPlacedResponse(BaseModel):
    bid: BidResponse
    was_extended: bool
    auction_end_time: datetime
