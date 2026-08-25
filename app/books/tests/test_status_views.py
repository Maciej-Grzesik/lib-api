from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient, codes
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book
from app.main import app

SERIAL_NUMBER = "123456"
CARD_NUMBER = "654321"


async def persist_book(session: AsyncSession, book: Book) -> Book:
    session.add(book)
    await session.flush()
    return book


def available_book() -> Book:
    return Book(
        serial_number=SERIAL_NUMBER,
        title="Dune",
        author="Frank Herbert",
    )


def borrowed_book() -> Book:
    return Book(
        serial_number=SERIAL_NUMBER,
        title="Dune",
        author="Frank Herbert",
        is_borrowed=True,
        borrower_card_number=CARD_NUMBER,
        borrowed_at=datetime(2026, 8, 24, 12, 30, tzinfo=UTC),
    )


def status_url() -> str:
    return app.url_path_for(
        "update_book_status",
        serial_number=SERIAL_NUMBER,
    )


async def test_borrow_book(client: AsyncClient, session: AsyncSession) -> None:
    await persist_book(session, available_book())

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": CARD_NUMBER},
    )

    assert response.status_code == codes.OK
    assert response.json()["is_borrowed"] is True


async def test_borrow_book_returns_borrower_card_number(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": CARD_NUMBER},
    )

    assert response.json()["borrower_card_number"] == CARD_NUMBER


async def test_borrow_book_sets_borrowed_at_automatically(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())
    before_request = datetime.now(UTC)

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": CARD_NUMBER},
    )

    after_request = datetime.now(UTC)
    borrowed_at = datetime.fromisoformat(response.json()["borrowed_at"])
    assert before_request <= borrowed_at <= after_request


async def test_borrowed_at_is_serialized_as_utc(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": CARD_NUMBER},
    )

    serialized_borrowed_at = response.json()["borrowed_at"]
    borrowed_at = datetime.fromisoformat(serialized_borrowed_at)
    assert serialized_borrowed_at.endswith("Z")
    assert borrowed_at.utcoffset() == timedelta(0)


async def test_borrow_book_without_card_number_is_rejected(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(status_url(), json={"is_borrowed": True})

    assert response.status_code == codes.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "card_number",
    ["12345", "1234567", "12A456"],
)
async def test_borrow_book_with_invalid_card_number_is_rejected(
    client: AsyncClient,
    session: AsyncSession,
    card_number: str,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": card_number},
    )

    assert response.status_code == codes.UNPROCESSABLE_ENTITY


async def test_borrow_book_accepts_card_number_with_leading_zero(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": "012345"},
    )

    assert response.status_code == codes.OK
    assert response.json()["borrower_card_number"] == "012345"


async def test_borrow_already_borrowed_book_returns_conflict(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, borrowed_book())

    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": CARD_NUMBER},
    )

    assert response.status_code == codes.CONFLICT


async def test_return_book(client: AsyncClient, session: AsyncSession) -> None:
    await persist_book(session, borrowed_book())

    response = await client.patch(status_url(), json={"is_borrowed": False})

    assert response.status_code == codes.OK
    assert response.json()["is_borrowed"] is False


async def test_return_book_clears_borrower_card_number(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, borrowed_book())

    response = await client.patch(status_url(), json={"is_borrowed": False})

    assert response.json()["borrower_card_number"] is None


async def test_return_book_clears_borrowed_at(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, borrowed_book())

    response = await client.patch(status_url(), json={"is_borrowed": False})

    assert response.json()["borrowed_at"] is None


async def test_return_available_book_returns_conflict(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(status_url(), json={"is_borrowed": False})

    assert response.status_code == codes.CONFLICT


async def test_update_status_of_missing_book_returns_not_found(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        status_url(),
        json={"is_borrowed": True, "borrower_card_number": CARD_NUMBER},
    )

    assert response.status_code == codes.NOT_FOUND


async def test_client_cannot_set_borrowed_at(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await persist_book(session, available_book())

    response = await client.patch(
        status_url(),
        json={
            "is_borrowed": True,
            "borrower_card_number": CARD_NUMBER,
            "borrowed_at": "2026-08-24T12:30:00Z",
        },
    )

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
