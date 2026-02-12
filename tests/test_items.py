import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "Vintage Jacket",
            "description": "A nice jacket",
            "size": "M",
            "condition": "good",
            "category": "outerwear",
            "image_urls": ["https://example.com/img.jpg"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Vintage Jacket"
    assert data["size"] == "M"


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/items/",
        json={
            "title": "T-Shirt",
            "description": "Cotton tee",
            "size": "S",
            "condition": "like_new",
            "category": "tops",
        },
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/items/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_items_filter_category(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/items/",
        json={
            "title": "Sneakers",
            "description": "Running shoes",
            "size": "L",
            "condition": "new_with_tags",
            "category": "shoes",
        },
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/items/?category=shoes")
    assert resp.status_code == 200
    for item in resp.json():
        assert item["category"] == "shoes"


@pytest.mark.asyncio
async def test_get_item(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "Dress",
            "description": "Summer dress",
            "size": "XS",
            "condition": "fair",
            "category": "dresses",
        },
        headers=auth_headers,
    )
    item_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/items/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == item_id


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "Old Title",
            "description": "desc",
            "size": "M",
            "condition": "good",
            "category": "tops",
        },
        headers=auth_headers,
    )
    item_id = create_resp.json()["id"]
    resp = await client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "New Title"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_item_forbidden(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    create_resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "My Item",
            "description": "desc",
            "size": "M",
            "condition": "good",
            "category": "tops",
        },
        headers=auth_headers,
    )
    item_id = create_resp.json()["id"]
    resp = await client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Hacked"},
        headers=second_auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/v1/items/",
        json={
            "title": "To Delete",
            "description": "desc",
            "size": "M",
            "condition": "poor",
            "category": "other",
        },
        headers=auth_headers,
    )
    item_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/items/{item_id}")
    assert resp.status_code == 404
