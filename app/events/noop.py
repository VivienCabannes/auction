from datetime import datetime
from decimal import Decimal

from app.events.interface import EventPublisher


class NoOpEventPublisher(EventPublisher):
    async def publish_bid_placed(
        self,
        auction_id: int,
        bid_id: int,
        bidder_id: int,
        amount: Decimal,
        new_end_time: datetime,
        was_extended: bool,
    ) -> None:
        pass

    async def publish_auction_ended(
        self,
        auction_id: int,
        winner_id: int | None,
        final_price: Decimal | None,
    ) -> None:
        pass
