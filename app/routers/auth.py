from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.exceptions import conflict, unauthorized
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    get_user_by_username,
    register_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_email(db, data.email):
        raise conflict("Email already registered")
    if await get_user_by_username(db, data.username):
        raise conflict("Username already taken")
    user = await register_user(db, data.email, data.username, data.password)
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.email, data.password)
    if user is None:
        raise unauthorized("Invalid email or password")
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
