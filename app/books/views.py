from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book
from app.books.schemas import BookResponse
from app.core.database_session import new_async_session

router = APIRouter()


@router.get("", response_model=list[BookResponse])
async def read_books(
    session: Annotated[AsyncSession, Depends(new_async_session)],
) -> list[Book]:
    books = await session.scalars(select(Book))

    return list(books.all())
