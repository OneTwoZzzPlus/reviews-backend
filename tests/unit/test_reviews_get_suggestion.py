from unittest.mock import MagicMock
from enums import SuggestionStatus
from services.reviews import ReviewsService


async def test_get_suggestion_not_found(mock_db):
    mock_db.get.return_value = None
    service = ReviewsService(mock_db)

    res = await service.get_suggestion(1)
    assert res is None


async def test_get_suggestion_with_subs(mock_db):
    mock_s = MagicMock()
    mock_s.id = 1
    mock_s.status = SuggestionStatus.delayed
    mock_s.user_isu = 100
    mock_s.moderator_isu = None
    mock_s.text = "Текст"
    mock_s.teacher_id = 10
    mock_s.teacher_title = "Препод"
    mock_s.subject_id = 20
    mock_s.subject_title = "Предмет"
    mock_s.subs_id = "30;"
    mock_s.subs_title = "Под1;Под2"
    mock_s.comment_id = None

    mock_db.get.return_value = mock_s
    service = ReviewsService(mock_db)

    res = await service.get_suggestion(1)

    assert res is not None
    assert res.id == 1
    assert len(res.subs) == 2
    assert res.subs[0].id == 30
    assert res.subs[0].title == "Под1"
    assert res.subs[1].id is None
    assert res.subs[1].title == "Под2"
