import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import select

from app.database import async_session_factory
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.events import get_event_publisher
from app.routers import auth, auctions, items

logger = logging.getLogger(__name__)


async def auction_lifecycle_loop():
    while True:
        try:
            await process_auction_transitions()
        except Exception:
            logger.exception("Error in auction lifecycle loop")
        await asyncio.sleep(30)


async def process_auction_transitions():
    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)
        publisher = get_event_publisher()

        # Activate pending auctions whose start_time has passed
        result = await db.execute(
            select(Auction)
            .where(
                Auction.status == AuctionStatus.PENDING,
                Auction.start_time <= now,
            )
            .with_for_update(skip_locked=True)
        )
        for auction in result.scalars().all():
            auction.status = AuctionStatus.ACTIVE

        # Resolve active auctions whose end_time has passed
        result = await db.execute(
            select(Auction)
            .where(
                Auction.status == AuctionStatus.ACTIVE,
                Auction.end_time <= now,
            )
            .with_for_update(skip_locked=True)
        )
        for auction in result.scalars().all():
            bid_result = await db.execute(
                select(Bid)
                .where(Bid.auction_id == auction.id)
                .order_by(Bid.amount.desc())
                .limit(1)
            )
            winning_bid = bid_result.scalar_one_or_none()
            auction.status = AuctionStatus.ENDED
            if winning_bid:
                auction.winner_id = winning_bid.bidder_id
                auction.current_highest_bid = winning_bid.amount

            await db.commit()

            await publisher.publish_auction_ended(
                auction_id=auction.id,
                winner_id=auction.winner_id,
                final_price=auction.current_highest_bid,
            )

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(auction_lifecycle_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Second-Hand Clothes Auction API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(auctions.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
