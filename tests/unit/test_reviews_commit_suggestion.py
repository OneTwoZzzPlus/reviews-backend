from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from schemas.reviews import CommitedItem, SuggestionCommitRequest
from services.reviews import ReviewsService


async def test_commit_suggestion_not_found(mock_db):
    mock_db.get.return_value = None
    service = ReviewsService(mock_db)

    body = SuggestionCommitRequest(
        teacher=CommitedItem(id=1, title="Т"),
        subject=CommitedItem(id=2, title="П"),
        subs=[],
        text="Отзыв",
    )
    res = await service.commit_suggestion(isu=99, iid=1, body=body)
    assert res is None


async def test_commit_suggestion_success(mock_db):
    mock_s = MagicMock()
    mock_s.date = "12:00 01.01.2025"
    mock_s.source_id = 1
    mock_db.get.return_value = mock_s

    service = ReviewsService(mock_db)

    body = SuggestionCommitRequest(
        teacher=CommitedItem(id=1, title="Т"),
        subject=CommitedItem(id=2, title="П"),
        subs=[CommitedItem(id=3, title="С")],
        text="Отзыв",
    )

    _ = await service.commit_suggestion(isu=99, iid=1, body=body)

    assert mock_db.flush.call_count == 1
    assert mock_db.commit.call_count == 1
    assert mock_s.status == "accepted"


async def test_commit_suggestion_integrity_error(mock_db):
    mock_db.get.return_value = MagicMock()
    mock_db.flush.side_effect = IntegrityError(None, None, None)

    service = ReviewsService(mock_db)
    body = SuggestionCommitRequest(
        teacher=CommitedItem(id=1, title="Т"),
        subject=CommitedItem(id=2, title="П"),
        subs=[],
        text="Отзыв",
    )

    res = await service.commit_suggestion(isu=99, iid=1, body=body)
    assert mock_db.rollback.call_count == 1
    assert res is None
