import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "username": "newuser", "password": "pass123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["username"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@test.com", "username": "user1", "password": "pass123"},
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@test.com", "username": "user2", "password": "pass123"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@test.com", "username": "loginuser", "password": "pass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.com", "password": "pass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@test.com", "username": "wronguser", "password": "pass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@test.com", "password": "bad"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@test.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403 or resp.status_code == 401
