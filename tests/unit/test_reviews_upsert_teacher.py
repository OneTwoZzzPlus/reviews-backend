from unittest.mock import AsyncMock

from schemas.reviews import TeacherUpdateRequest
from services.reviews import ReviewsService


async def test_upsert_teacher_success(mock_db):
    service = ReviewsService(mock_db)
    service.reload_cache = AsyncMock()

    data = TeacherUpdateRequest(id=5, title="Новый Учитель")
    res = await service.upsert_teacher(data)

    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 1
    service.reload_cache.assert_called_once()
    assert res.id == 5
