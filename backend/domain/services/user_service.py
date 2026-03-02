import asyncpg
from fastapi import HTTPException

from backend.domain.repositories.user_repository import UserRepository


async def get_current_user(user_id: str, conn: asyncpg.Connection):
    user = await UserRepository.get_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
