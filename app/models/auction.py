import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuctionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class Auction(Base):
    __tablename__ = "auctions"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), unique=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    start_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    current_highest_bid: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    original_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[AuctionStatus] = mapped_column(
        Enum(AuctionStatus, native_enum=False), index=True, default=AuctionStatus.PENDING
    )
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
