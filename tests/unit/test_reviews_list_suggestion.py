from unittest.mock import MagicMock

from enums import SuggestionStatus
from services.reviews import ReviewsService


async def test_list_suggestion_success(mock_db):
    mock_s1 = MagicMock()
    mock_s1.id = 1
    mock_s1.status = SuggestionStatus.delayed
    mock_s1.teacher_title = "Иванов"
    mock_s1.source_id = 1

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_s1]
    mock_db.scalars.return_value = mock_scalars

    service = ReviewsService(mock_db)
    res = await service.list_suggestion(delayed=True, accepted=False, rejected=False)

    assert len(res.items) == 1
    assert res.items[0].id == 1
    assert res.items[0].status == SuggestionStatus.delayed
