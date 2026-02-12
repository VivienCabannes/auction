from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.exceptions import unauthorized
from app.models.user import User
from app.services.auth import decode_access_token, get_user_by_id

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized("Invalid or expired token")
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized("User not found")
    return user
