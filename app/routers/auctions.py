from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.events import get_event_publisher
from app.events.interface import EventPublisher
from app.exceptions import bad_request, forbidden, not_found
from app.models.auction import AuctionStatus
from app.models.user import User
from app.schemas.auction import AuctionCreate, AuctionResponse
from app.schemas.bid import BidCreate, BidPlacedResponse, BidResponse
from app.services import auction as auction_service
from app.services import bid as bid_service
from app.services.item import get_item

router = APIRouter(prefix="/api/v1/auctions", tags=["auctions"])


@router.post("/", response_model=AuctionResponse, status_code=201)
async def create_auction(
    data: AuctionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await get_item(db, data.item_id)
    if item is None:
        raise not_found("Item not found")
    if item.seller_id != current_user.id:
        raise forbidden("Not your item")
    if data.end_time <= data.start_time:
        raise bad_request("end_time must be after start_time")
    existing = await auction_service.get_active_auction_for_item(db, data.item_id)
    if existing:
        raise bad_request("Item already has an active or pending auction")
    auction = await auction_service.create_auction(
        db,
        seller_id=current_user.id,
        item_id=data.item_id,
        start_price=data.start_price,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    return auction


@router.get("/", response_model=list[AuctionResponse])
async def list_auctions(
    status: AuctionStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    auctions = await auction_service.list_auctions(
        db, status=status, skip=skip, limit=limit
    )
    return auctions


@router.get("/{auction_id}", response_model=AuctionResponse)
async def get_auction(auction_id: int, db: AsyncSession = Depends(get_db)):
    auction = await auction_service.get_auction(db, auction_id)
    if auction is None:
        raise not_found("Auction not found")
    return auction


@router.post("/{auction_id}/cancel", response_model=AuctionResponse)
async def cancel_auction(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auction = await auction_service.get_auction(db, auction_id)
    if auction is None:
        raise not_found("Auction not found")
    if auction.seller_id != current_user.id:
        raise forbidden("Not your auction")
    if auction.status not in (AuctionStatus.PENDING, AuctionStatus.ACTIVE):
        raise bad_request("Auction cannot be cancelled")
    if await auction_service.has_bids(db, auction.id):
        raise bad_request("Cannot cancel auction with bids")
    auction = await auction_service.cancel_auction(db, auction)
    return auction


@router.post("/{auction_id}/bids", response_model=BidPlacedResponse, status_code=201)
async def place_bid(
    auction_id: int,
    data: BidCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: EventPublisher = Depends(get_event_publisher),
):
    result = await bid_service.place_bid(
        db,
        auction_id=auction_id,
        bidder_id=current_user.id,
        amount=data.amount,
        publisher=publisher,
    )
    return result


@router.get("/{auction_id}/bids", response_model=list[BidResponse])
async def list_bids(
    auction_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    bids = await bid_service.list_bids(db, auction_id=auction_id, skip=skip, limit=limit)
    return bids
