from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError
from enums import SuggestionStatus
from schemas.reviews import SuggestionCancelRequest
from services.reviews import ReviewsService


async def test_cancel_suggestion_success(mock_db):
    mock_s = MagicMock()
    mock_db.get.return_value = mock_s

    service = ReviewsService(mock_db)
    body = SuggestionCancelRequest(status=SuggestionStatus.rejected)

    res = await service.cancel_suggestion(isu=99, iid=1, body=body)

    assert mock_s.status == SuggestionStatus.rejected
    assert mock_s.moderator_isu == 99
    assert mock_db.commit.call_count == 1
    assert res.status == SuggestionStatus.rejected


async def test_cancel_suggestion_not_found(mock_db):
    mock_db.get.return_value = None
    service = ReviewsService(mock_db)

    res = await service.cancel_suggestion(isu=99, iid=1, body=SuggestionCancelRequest())
    assert res is None


async def test_cancel_suggestion_integrity_error(mock_db):
    mock_db.get.return_value = MagicMock()
    mock_db.commit.side_effect = IntegrityError(None, None, None)

    service = ReviewsService(mock_db)
    res = await service.cancel_suggestion(isu=99, iid=1, body=SuggestionCancelRequest())

    assert mock_db.rollback.call_count == 1
    assert res is None
