import uuid as uuid_pkg
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        sa.CheckConstraint(
            "serial_number ~ '^[0-9]{6}$'",
            name="ck_books_serial_number_six_digits",
        ),
        sa.CheckConstraint(
            "length(btrim(title)) > 0",
            name="ck_books_title_not_blank",
        ),
        sa.CheckConstraint(
            "length(btrim(author)) > 0",
            name="ck_books_author_not_blank",
        ),
        sa.CheckConstraint(
            "borrower_card_number IS NULL OR borrower_card_number ~ '^[0-9]{6}$'",
            name="ck_books_borrower_card_number_six_digits",
        ),
        sa.UniqueConstraint("serial_number", name="uq_books_serial_number"),
    )

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        default=uuid_pkg.uuid4,
    )
    serial_number: Mapped[str] = mapped_column(sa.String(6), nullable=False)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    author: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_borrowed: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.false(),
    )
    borrower_card_number: Mapped[str | None] = mapped_column(
        sa.String(6),
        nullable=True,
        default=None,
    )
    borrowed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
        default=None,
    )
