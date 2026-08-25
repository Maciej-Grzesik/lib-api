from datetime import UTC, datetime

from httpx import AsyncClient, codes
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book
from app.main import app


async def add_book(
    session: AsyncSession,
    book: Book,
) -> Book:
    session.add(book)
    await session.flush()
    return book


async def test_read_books_returns_empty_list(client: AsyncClient) -> None:
    response = await client.get(app.url_path_for("read_books"))

    assert response.status_code == codes.OK
    assert response.json() == []


async def test_read_books_returns_one_book(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    borrowed_at = datetime(2026, 8, 24, 12, 30, tzinfo=UTC)
    book = await add_book(
        session,
        Book(
            serial_number="123456",
            title="Dune",
            author="Frank Herbert",
            is_borrowed=True,
            borrower_card_number="654321",
            borrowed_at=borrowed_at,
        ),
    )

    response = await client.get(app.url_path_for("read_books"))

    assert response.status_code == codes.OK
    assert response.json() == [
        {
            "uuid": str(book.uuid),
            "serial_number": "123456",
            "title": "Dune",
            "author": "Frank Herbert",
            "is_borrowed": True,
            "borrower_card_number": "654321",
            "borrowed_at": "2026-08-24T12:30:00Z",
        }
    ]


async def test_read_books_returns_multiple_books(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    books = [
        Book(serial_number="123456", title="Dune", author="Frank Herbert"),
        Book(serial_number="654321", title="Solaris", author="Stanisław Lem"),
        Book(serial_number="111222", title="The Hobbit", author="J.R.R. Tolkien"),
    ]
    for book in books:
        await add_book(session, book)

    response = await client.get(app.url_path_for("read_books"))

    assert response.status_code == codes.OK
    assert len(response.json()) == len(books)
    assert {book["serial_number"] for book in response.json()} == {
        "123456",
        "654321",
        "111222",
    }


async def test_read_books_uses_book_response_model(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await add_book(
        session,
        Book(serial_number="123456", title="Witcher", author="A. Sapkowski"),
    )

    response = await client.get(app.url_path_for("read_books"))

    assert set(response.json()[0]) == {
        "uuid",
        "serial_number",
        "title",
        "author",
        "is_borrowed",
        "borrower_card_number",
        "borrowed_at",
    }


async def test_read_books_preserves_leading_zero_in_serial_number(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await add_book(
        session,
        Book(serial_number="012345", title="Witcher", author="A. Sapkowski"),
    )

    response = await client.get(app.url_path_for("read_books"))

    assert response.status_code == codes.OK
    assert response.json()[0]["serial_number"] == "012345"
