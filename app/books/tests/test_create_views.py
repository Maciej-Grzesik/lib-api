import pytest
from httpx import AsyncClient, codes

from app.main import app


def valid_book_data(serial_number: str = "123456") -> dict[str, object]:
    return {
        "serial_number": serial_number,
        "title": "Dune",
        "author": "Frank Herbert",
    }


async def test_create_book_returns_created(client: AsyncClient) -> None:
    response = await client.post(
        app.url_path_for("create_book"),
        json=valid_book_data(),
    )

    assert response.status_code == codes.CREATED


async def test_create_book_returns_available_book(client: AsyncClient) -> None:
    response = await client.post(
        app.url_path_for("create_book"),
        json=valid_book_data(),
    )

    assert response.json() == {
        "uuid": response.json()["uuid"],
        "serial_number": "123456",
        "title": "Dune",
        "author": "Frank Herbert",
        "is_borrowed": False,
        "borrower_card_number": None,
        "borrowed_at": None,
    }


async def test_created_book_is_persisted(client: AsyncClient) -> None:
    await client.post(app.url_path_for("create_book"), json=valid_book_data())

    response = await client.get(app.url_path_for("read_books"))

    assert response.status_code == codes.OK
    assert response.json()[0]["serial_number"] == "123456"


async def test_create_duplicate_book_returns_conflict(client: AsyncClient) -> None:
    await client.post(app.url_path_for("create_book"), json=valid_book_data())

    response = await client.post(
        app.url_path_for("create_book"),
        json=valid_book_data(),
    )

    assert response.status_code == codes.CONFLICT


async def test_session_is_usable_after_duplicate_conflict(client: AsyncClient) -> None:
    await client.post(app.url_path_for("create_book"), json=valid_book_data())
    await client.post(app.url_path_for("create_book"), json=valid_book_data())

    response = await client.post(
        app.url_path_for("create_book"),
        json=valid_book_data(serial_number="654321"),
    )

    assert response.status_code == codes.CREATED


@pytest.mark.parametrize(
    "field,value",
    [
        ("is_borrowed", True),
        ("borrower_card_number", "123456"),
        ("borrowed_at", "2026-08-24T12:30:00Z"),
    ],
)
async def test_create_book_rejects_server_managed_fields(
    client: AsyncClient,
    field: str,
    value: object,
) -> None:
    data = valid_book_data()
    data[field] = value

    response = await client.post(app.url_path_for("create_book"), json=data)

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert isinstance(response.json()["detail"], list)


async def test_create_book_returns_standard_validation_error(
    client: AsyncClient,
) -> None:
    response = await client.post(
        app.url_path_for("create_book"),
        json=valid_book_data(serial_number="12345"),
    )

    assert response.status_code == codes.UNPROCESSABLE_ENTITY
    assert isinstance(response.json()["detail"], list)
