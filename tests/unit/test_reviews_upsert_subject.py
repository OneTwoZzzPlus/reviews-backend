from unittest.mock import AsyncMock

from schemas.reviews import SubjectUpdateRequest
from services.reviews import ReviewsService


async def test_upsert_subject_new_item(mock_db):
    service = ReviewsService(mock_db)
    service.reload_cache = AsyncMock()

    data = SubjectUpdateRequest(id=None, title="Новый Предмет")
    _ = await service.upsert_subject(data)

    assert mock_db.add.call_count == 1
    assert mock_db.commit.call_count == 1
    service.reload_cache.assert_called_once()


async def test_upsert_subject_existing_item(mock_db):
    service = ReviewsService(mock_db)
    service.reload_cache = AsyncMock()

    data = SubjectUpdateRequest(id=10, title="Обновленный Предмет")
    res = await service.upsert_subject(data)

    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 1
    service.reload_cache.assert_called_once()
    assert res.id == 10
