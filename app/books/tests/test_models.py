from app.books.models import Book


def test_book_model_metadata() -> None:
    assert Book.__tablename__ == "books"
    assert set(Book.__table__.columns.keys()) == {
        "uuid",
        "serial_number",
        "title",
        "author",
        "is_borrowed",
        "borrower_card_number",
        "borrowed_at",
    }
    assert list(Book.__table__.primary_key) == [Book.__table__.c.uuid]
