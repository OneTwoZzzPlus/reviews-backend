from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.exc import IntegrityError

from services.reviews import ReviewsService


async def test_teacher_rate_success(mock_db):
    service = ReviewsService(mock_db)

    mock_response = MagicMock()
    mock_response.rating = 4.8
    mock_response.user_rating = 5

    service.teacher = AsyncMock(return_value=mock_response)

    res = await service.teacher_rate(isu=100, iid=1, rating=5)

    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 1
    assert res.rating == 4.8
    assert res.user_rating == 5


async def test_teacher_rate_integrity_error(mock_db):
    mock_db.execute.side_effect = IntegrityError(None, None, None)
    service = ReviewsService(mock_db)

    res = await service.teacher_rate(isu=100, iid=1, rating=5)

    assert mock_db.rollback.call_count == 1
    assert res is None
