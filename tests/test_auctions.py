from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


def future(minutes: int = 60) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def past(minutes: int = 60) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


async def create_test_item(client: AsyncClient, headers: dict) -> int:
    resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "Auction Item",
            "description": "For auction",
            "size": "M",
            "condition": "good",
            "category": "tops",
        },
        headers=headers,
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_auction(client: AsyncClient, auth_headers: dict):
    item_id = await create_test_item(client, auth_headers)
    resp = await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": past(5),
            "end_time": future(60),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["item_id"] == item_id
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_auction_pending(client: AsyncClient, auth_headers: dict):
    item_id = await create_test_item(client, auth_headers)
    resp = await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": future(30),
            "end_time": future(120),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_create_auction_not_owner(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    item_id = await create_test_item(client, auth_headers)
    resp = await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": future(5),
            "end_time": future(60),
        },
        headers=second_auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_auctions(client: AsyncClient, auth_headers: dict):
    item_id = await create_test_item(client, auth_headers)
    await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "5.00",
            "start_time": past(5),
            "end_time": future(60),
        },
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/auctions/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_cancel_auction_no_bids(client: AsyncClient, auth_headers: dict):
    item_id = await create_test_item(client, auth_headers)
    create_resp = await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": past(5),
            "end_time": future(60),
        },
        headers=auth_headers,
    )
    auction_id = create_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/auctions/{auction_id}/cancel", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_duplicate_auction_for_item(client: AsyncClient, auth_headers: dict):
    item_id = await create_test_item(client, auth_headers)
    await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": past(5),
            "end_time": future(60),
        },
        headers=auth_headers,
    )
    resp = await client.post(
        "/api/v1/auctions/",
        json={
            "item_id": item_id,
            "start_price": "10.00",
            "start_time": past(5),
            "end_time": future(60),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400
