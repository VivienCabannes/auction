from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


def future(minutes: int = 60) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def past(minutes: int = 60) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


async def setup_auction(
    client: AsyncClient, seller_headers: dict, start_minutes_ago: int = 5, end_minutes_ahead: int = 60
) -> int:
    item_resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "Bid Item",
            "description": "For bidding",
            "size": "M",
            "condition": "good",
            "category": "tops",
        },
        headers=seller_headers,
    )
    item_id = item_resp.json()["id"]
    auction_resp = await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": past(start_minutes_ago),
            "end_time": future(end_minutes_ahead),
        },
        headers=seller_headers,
    )
    return auction_resp.json()["id"]


@pytest.mark.asyncio
async def test_place_bid(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    auction_id = await setup_auction(client, auth_headers)
    resp = await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "15.00"},
        headers=second_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["bid"]["amount"] == "15.00"
    assert data["was_extended"] is False


@pytest.mark.asyncio
async def test_bid_too_low(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    auction_id = await setup_auction(client, auth_headers)
    resp = await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "5.00"},
        headers=second_auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_seller_cannot_bid(client: AsyncClient, auth_headers: dict):
    auction_id = await setup_auction(client, auth_headers)
    resp = await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "15.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bid_history(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    auction_id = await setup_auction(client, auth_headers)
    await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "15.00"},
        headers=second_auth_headers,
    )
    await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "20.00"},
        headers=second_auth_headers,
    )
    resp = await client.get(f"/api/v1/auctions/{auction_id}/bids")
    assert resp.status_code == 200
    bids = resp.json()
    assert len(bids) == 2
    assert float(bids[0]["amount"]) > float(bids[1]["amount"])


@pytest.mark.asyncio
async def test_soft_close_extension(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    # Create auction ending in 3 minutes (within the 5-minute soft-close window)
    auction_id = await setup_auction(client, auth_headers, end_minutes_ahead=3)
    resp = await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "15.00"},
        headers=second_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["was_extended"] is True


@pytest.mark.asyncio
async def test_cancel_auction_with_bids_fails(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    auction_id = await setup_auction(client, auth_headers)
    await client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"amount": "15.00"},
        headers=second_auth_headers,
    )
    resp = await client.post(
        f"/api/v1/auctions/{auction_id}/cancel", headers=auth_headers
    )
    assert resp.status_code == 400
