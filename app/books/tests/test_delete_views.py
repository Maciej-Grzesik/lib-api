from datetime import UTC, datetime

from httpx import AsyncClient, codes
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book
from app.main import app

SERIAL_NUMBER = "123456"


async def persist_book(
    session: AsyncSession,
    *,
    is_borrowed: bool = False,
) -> Book:
    book = Book(
        serial_number=SERIAL_NUMBER,
        title="Dune",
        author="Frank Herbert",
        is_borrowed=is_borrowed,
        borrower_card_number="654321" if is_borrowed else None,
        borrowed_at=(
            datetime(2026, 8, 24, 12, 30, tzinfo=UTC) if is_borrowed else None
        ),
    )
    session.add(book)
    await session.flush()
    return book


def delete_url() -> str:
    return app.url_path_for("delete_book", serial_number=SERIAL_NUMBER)


async def test_delete_available_book(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    book = await persist_book(session)

    await client.delete(delete_url())

    assert await session.get(Book, book.uuid) is None


async def test_delete_book_returns_no_content_status(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session)

    response = await client.delete(delete_url())

    assert response.status_code == codes.NO_CONTENT


async def test_delete_book_returns_empty_body(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session)

    response = await client.delete(delete_url())

    assert response.content == b""


async def test_deleted_book_is_not_returned_by_read_books(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session)
    await client.delete(delete_url())

    response = await client.get(app.url_path_for("read_books"))

    assert response.status_code == codes.OK
    assert response.json() == []


async def test_delete_missing_book_returns_not_found(client: AsyncClient) -> None:
    response = await client.delete(delete_url())

    assert response.status_code == codes.NOT_FOUND


async def test_delete_borrowed_book(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    book = await persist_book(session, is_borrowed=True)

    response = await client.delete(delete_url())

    assert response.status_code == codes.NO_CONTENT
    assert await session.get(Book, book.uuid) is None
