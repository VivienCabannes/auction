"""initial_schema

Revision ID: b1cc668221ca
Revises:
Create Date: 2026-02-12 23:10:50.767586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1cc668221ca'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "seller_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("size", sa.String(10), nullable=False),
        sa.Column("condition", sa.String(20), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column(
            "image_urls",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_items_seller_id", "items", ["seller_id"])

    op.create_table(
        "auctions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "item_id", sa.Integer(), sa.ForeignKey("items.id"), nullable=False
        ),
        sa.Column(
            "seller_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("start_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("current_highest_bid", sa.Numeric(10, 2), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("original_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "winner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_auctions_item_id", "auctions", ["item_id"], unique=True)
    op.create_index("ix_auctions_seller_id", "auctions", ["seller_id"])
    op.create_index("ix_auctions_status", "auctions", ["status"])

    op.create_table(
        "bids",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "auction_id",
            sa.Integer(),
            sa.ForeignKey("auctions.id"),
            nullable=False,
        ),
        sa.Column(
            "bidder_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_bids_auction_id", "bids", ["auction_id"])
    op.create_index("ix_bids_bidder_id", "bids", ["bidder_id"])


def downgrade() -> None:
    op.drop_table("bids")
    op.drop_table("auctions")
    op.drop_table("items")
    op.drop_table("users")
