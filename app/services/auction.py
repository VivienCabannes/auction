from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def create_auction(db: AsyncSession, seller_id: int, **kwargs) -> Auction:
    auction = Auction(
        seller_id=seller_id,
        original_end_time=kwargs["end_time"],
        status=AuctionStatus.PENDING,
        **kwargs,
    )
    now = datetime.now(timezone.utc)
    if _ensure_utc(auction.start_time) <= now:
        auction.status = AuctionStatus.ACTIVE
    db.add(auction)
    await db.commit()
    await db.refresh(auction)
    return auction


async def get_auction(db: AsyncSession, auction_id: int) -> Auction | None:
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if auction:
        await maybe_resolve_auction(db, auction)
    return auction


async def list_auctions(
    db: AsyncSession,
    status: AuctionStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Auction]:
    stmt = select(Auction)
    if status:
        stmt = stmt.where(Auction.status == status)
    stmt = stmt.order_by(Auction.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_active_auction_for_item(
    db: AsyncSession, item_id: int
) -> Auction | None:
    result = await db.execute(
        select(Auction).where(
            Auction.item_id == item_id,
            Auction.status.in_([AuctionStatus.PENDING, AuctionStatus.ACTIVE]),
        )
    )
    return result.scalar_one_or_none()


async def cancel_auction(db: AsyncSession, auction: Auction) -> Auction:
    auction.status = AuctionStatus.CANCELLED
    await db.commit()
    await db.refresh(auction)
    return auction


async def has_bids(db: AsyncSession, auction_id: int) -> bool:
    result = await db.execute(
        select(Bid.id).where(Bid.auction_id == auction_id).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def maybe_resolve_auction(db: AsyncSession, auction: Auction) -> None:
    now = datetime.now(timezone.utc)
    if auction.status == AuctionStatus.PENDING and _ensure_utc(auction.start_time) <= now:
        auction.status = AuctionStatus.ACTIVE
        await db.commit()
        await db.refresh(auction)
    if auction.status == AuctionStatus.ACTIVE and _ensure_utc(auction.end_time) <= now:
        await resolve_auction(db, auction)


async def resolve_auction(db: AsyncSession, auction: Auction) -> None:
    result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction.id)
        .order_by(Bid.amount.desc())
        .limit(1)
    )
    winning_bid = result.scalar_one_or_none()
    auction.status = AuctionStatus.ENDED
    if winning_bid:
        auction.winner_id = winning_bid.bidder_id
        auction.current_highest_bid = winning_bid.amount
    await db.commit()
    await db.refresh(auction)
