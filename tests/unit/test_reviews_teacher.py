from unittest.mock import MagicMock

from services.reviews import ReviewsService


async def test_teacher_not_found(mock_db):
    mock_db.scalar.return_value = None
    service = ReviewsService(mock_db)

    res = await service.teacher(1)
    assert res is None


async def test_teacher_found_success(mock_db):
    mock_teacher = MagicMock()
    mock_teacher.id = 1
    mock_teacher.name = "Иванов И.И."
    mock_teacher.summaries = []
    mock_teacher.comments = []

    mock_db.scalar.return_value = mock_teacher
    service = ReviewsService(mock_db)

    res = await service.teacher(1)

    assert res is not None
    assert res.id == 1

    assert res.name == "Иванов И.И."
