from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

SixDigitIdentifier = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{6}$"),
]
NonBlankString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class BookCreate(BaseModel):
    serial_number: SixDigitIdentifier
    title: NonBlankString
    author: NonBlankString


class BookResponse(BaseModel):
    uuid: UUID
    serial_number: SixDigitIdentifier
    title: NonBlankString
    author: NonBlankString
    is_borrowed: bool
    borrower_card_number: SixDigitIdentifier | None
    borrowed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class BookStatusUpdate(BaseModel):
    is_borrowed: bool
    borrower_card_number: SixDigitIdentifier | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_borrower_card_number_for_borrowing(self) -> Self:
        if self.is_borrowed and self.borrower_card_number is None:
            raise ValueError("borrower_card_number is required when borrowing a book")
        return self
