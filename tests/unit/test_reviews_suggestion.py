from schemas.reviews import InputItem, SuggestionRequest
from services.reviews import ReviewsService


async def test_add_suggestion_success(mock_db):
    service = ReviewsService(mock_db)

    data = SuggestionRequest(
        teacher=InputItem(id=1, title="Учитель"),
        subject=InputItem(id=2, title="Предмет"),
        subs=[InputItem(id=3, title="Доп1;тест"), InputItem(id=None, title="Доп2")],
        text="Отличный преподаватель",
    )

    res = await service.add_suggestion(data=data)

    assert mock_db.add.call_count == 1
    assert mock_db.commit.call_count == 1
    assert isinstance(res.id, (int, type(None)))
