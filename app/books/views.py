from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book
from app.books.schemas import (
    BookCreate,
    BookResponse,
    BookStatusUpdate,
    SixDigitIdentifier,
)
from app.core.database_session import new_async_session

router = APIRouter()


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate,
    session: Annotated[AsyncSession, Depends(new_async_session)],
) -> Book:
    book = Book(
        serial_number=data.serial_number,
        title=data.title,
        author=data.author,
    )
    session.add(book)

    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Book with this serial number already exists",
        ) from error

    return book


@router.get("", response_model=list[BookResponse])
async def read_books(
    session: Annotated[AsyncSession, Depends(new_async_session)],
) -> list[Book]:
    books = await session.scalars(select(Book))

    return list(books.all())


@router.patch("/{serial_number}/status", response_model=BookResponse)
async def update_book_status(
    serial_number: SixDigitIdentifier,
    data: BookStatusUpdate,
    session: Annotated[AsyncSession, Depends(new_async_session)],
) -> Book:
    book = await session.scalar(
        select(Book).where(Book.serial_number == serial_number).with_for_update()
    )
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    if book.is_borrowed == data.is_borrowed:
        state = "borrowed" if book.is_borrowed else "available"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book is already {state}",
        )

    book.is_borrowed = data.is_borrowed
    if data.is_borrowed:
        book.borrower_card_number = data.borrower_card_number
        book.borrowed_at = datetime.now(UTC)
    else:
        book.borrower_card_number = None
        book.borrowed_at = None

    await session.commit()
    return book


@router.delete("/{serial_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    serial_number: SixDigitIdentifier,
    session: Annotated[AsyncSession, Depends(new_async_session)],
) -> None:
    book = await session.scalar(select(Book).where(Book.serial_number == serial_number))
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    await session.delete(book)
    await session.commit()
