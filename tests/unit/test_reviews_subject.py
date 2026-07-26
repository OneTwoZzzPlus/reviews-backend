from unittest.mock import MagicMock
from services.reviews import ReviewsService


async def test_subject_not_found(mock_db):
    mock_db.scalar.return_value = None
    service = ReviewsService(mock_db)

    res = await service.subject(1)
    assert res is None


async def test_subject_found_success(mock_db):
    mock_subject = MagicMock()
    mock_subject.id = 10
    mock_subject.title = "Алгебра"
    mock_subject.teachers = []

    mock_db.scalar.return_value = mock_subject
    service = ReviewsService(mock_db)

    res = await service.subject(10)

    assert res is not None
    assert res.id == 10
    assert res.title == "Алгебра"
    assert res.teachers == []
