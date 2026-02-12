import asyncio
from datetime import datetime
from decimal import Decimal

import firebase_admin
from firebase_admin import credentials, db as firebase_db

from app.events.interface import EventPublisher


class FirebaseEventPublisher(EventPublisher):
    def __init__(self, credentials_path: str, project_id: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(
                cred,
                {"databaseURL": f"https://{project_id}-default-rtdb.firebaseio.com"},
            )

    def _push_sync(self, path: str, data: dict) -> None:
        ref = firebase_db.reference(path)
        ref.push(data)

    async def publish_bid_placed(
        self,
        auction_id: int,
        bid_id: int,
        bidder_id: int,
        amount: Decimal,
        new_end_time: datetime,
        was_extended: bool,
    ) -> None:
        data = {
            "type": "bid_placed",
            "bid_id": bid_id,
            "bidder_id": bidder_id,
            "amount": str(amount),
            "new_end_time": new_end_time.isoformat(),
            "was_extended": was_extended,
        }
        await asyncio.to_thread(
            self._push_sync, f"/auctions/{auction_id}/events", data
        )

    async def publish_auction_ended(
        self,
        auction_id: int,
        winner_id: int | None,
        final_price: Decimal | None,
    ) -> None:
        data = {
            "type": "auction_ended",
            "winner_id": winner_id,
            "final_price": str(final_price) if final_price else None,
        }
        await asyncio.to_thread(
            self._push_sync, f"/auctions/{auction_id}/events", data
        )
