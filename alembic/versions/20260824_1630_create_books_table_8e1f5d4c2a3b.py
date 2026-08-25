"""create books table

Revision ID: 8e1f5d4c2a3b
Revises:
Create Date: 2026-08-24 16:30:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8e1f5d4c2a3b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("serial_number", sa.String(length=6), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column(
            "is_borrowed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("borrower_card_number", sa.String(length=6), nullable=True),
        sa.Column("borrowed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(btrim(author)) > 0",
            name="ck_books_author_not_blank",
        ),
        sa.CheckConstraint(
            "borrower_card_number IS NULL OR borrower_card_number ~ '^[0-9]{6}$'",
            name="ck_books_borrower_card_number_six_digits",
        ),
        sa.CheckConstraint(
            "serial_number ~ '^[0-9]{6}$'",
            name="ck_books_serial_number_six_digits",
        ),
        sa.CheckConstraint(
            "length(btrim(title)) > 0",
            name="ck_books_title_not_blank",
        ),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint("serial_number", name="uq_books_serial_number"),
    )


def downgrade() -> None:
    op.drop_table("books")
