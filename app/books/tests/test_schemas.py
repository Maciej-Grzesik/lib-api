import pytest
from pydantic import ValidationError

from app.books.schemas import BookCreate, BookStatusUpdate


@pytest.mark.parametrize("serial_number", ["123456", "012345"])
def test_book_create_accepts_six_digit_serial_number(serial_number: str) -> None:
    book = BookCreate(
        serial_number=serial_number,
        title="Witcher",
        author="A. Sapkowski",
    )

    assert book.serial_number == serial_number


@pytest.mark.parametrize(
    "serial_number",
    ["12345", "1234567", "12A456", "ありがとうご"],
)
def test_book_create_rejects_invalid_serial_number(serial_number: str) -> None:
    with pytest.raises(ValidationError):
        BookCreate(
            serial_number=serial_number,
            title="Witcher",
            author="A. Sapkowski",
        )


@pytest.mark.parametrize("field", ["title", "author"])
@pytest.mark.parametrize("value", ["", "   "])
def test_book_create_rejects_blank_title_and_author(
    field: str,
    value: str,
) -> None:
    data = {
        "serial_number": "123456",
        "title": "Witcher",
        "author": "A. Sapkowski",
        field: value,
    }

    with pytest.raises(ValidationError):
        BookCreate.model_validate(data)


@pytest.mark.parametrize("borrower_card_number", ["123456", "012345", None])
def test_book_status_update_accepts_valid_borrower_card_number(
    borrower_card_number: str | None,
) -> None:
    status = BookStatusUpdate(
        is_borrowed=borrower_card_number is not None,
        borrower_card_number=borrower_card_number,
    )

    assert status.borrower_card_number == borrower_card_number


@pytest.mark.parametrize(
    "borrower_card_number",
    ["12345", "1234567", "12A456", "ありがとうご"],
)
def test_book_status_update_rejects_invalid_borrower_card_number(
    borrower_card_number: str,
) -> None:
    with pytest.raises(ValidationError):
        BookStatusUpdate(
            is_borrowed=True,
            borrower_card_number=borrower_card_number,
        )
