from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.events.interface import EventPublisher
from app.exceptions import bad_request, forbidden, not_found
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.schemas.bid import BidPlacedResponse, BidResponse


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def place_bid(
    db: AsyncSession,
    auction_id: int,
    bidder_id: int,
    amount: Decimal,
    publisher: EventPublisher,
) -> BidPlacedResponse:
    # Lock the auction row
    result = await db.execute(
        select(Auction)
        .where(Auction.id == auction_id)
        .with_for_update()
    )
    auction = result.scalar_one_or_none()
    if auction is None:
        raise not_found("Auction not found")

    now = datetime.now(timezone.utc)

    if auction.status != AuctionStatus.ACTIVE:
        raise bad_request("Auction is not active")
    end_time = _ensure_utc(auction.end_time)
    if now >= end_time:
        raise bad_request("Auction has ended")
    if auction.seller_id == bidder_id:
        raise forbidden("Seller cannot bid on own auction")

    min_bid = auction.current_highest_bid or auction.start_price
    if amount <= min_bid:
        raise bad_request(f"Bid must be greater than {min_bid}")

    bid = Bid(auction_id=auction_id, bidder_id=bidder_id, amount=amount)
    db.add(bid)

    auction.current_highest_bid = amount

    # Soft-close check
    was_extended = False
    window = timedelta(minutes=settings.SOFT_CLOSE_WINDOW_MINUTES)
    if now >= end_time - window:
        extension = timedelta(minutes=settings.SOFT_CLOSE_EXTENSION_MINUTES)
        auction.end_time = end_time + extension
        was_extended = True

    await db.commit()
    await db.refresh(bid)
    await db.refresh(auction)

    await publisher.publish_bid_placed(
        auction_id=auction.id,
        bid_id=bid.id,
        bidder_id=bidder_id,
        amount=amount,
        new_end_time=auction.end_time,
        was_extended=was_extended,
    )

    return BidPlacedResponse(
        bid=BidResponse.model_validate(bid),
        was_extended=was_extended,
        auction_end_time=auction.end_time,
    )


async def list_bids(
    db: AsyncSession, auction_id: int, skip: int = 0, limit: int = 50
) -> list[Bid]:
    stmt = (
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(Bid.amount.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
