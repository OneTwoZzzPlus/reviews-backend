from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError
from services.reviews import ReviewsService


async def test_comment_vote_success(mock_db):
    mock_comment = MagicMock()
    mock_comment.karma = 10
    mock_comment.user_karma = 1
    mock_db.scalar.return_value = mock_comment

    service = ReviewsService(mock_db)
    res = await service.comment_vote(isu=100, iid=5, karma=1)

    assert mock_db.execute.call_count == 1
    assert mock_db.commit.call_count == 1
    assert res.karma == 10
    assert res.user_karma == 1


async def test_comment_vote_integrity_error(mock_db):
    mock_db.execute.side_effect = IntegrityError(None, None, None)
    service = ReviewsService(mock_db)

    res = await service.comment_vote(isu=100, iid=5, karma=1)

    assert mock_db.rollback.call_count == 1
    assert res is None
