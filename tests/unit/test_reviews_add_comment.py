from schemas.reviews import CommentAddRequest, CommitedItem
from services.reviews import ReviewsService


async def test_add_comment_success(mock_db):
    service = ReviewsService(mock_db)

    data = CommentAddRequest(
        source_id=1,
        date="10:00 01.01.2025",
        teacher=CommitedItem(id=1, title="Препод"),
        subject=CommitedItem(id=2, title="Предмет"),
        subs=[CommitedItem(id=3, title="Доп")],
        text="Текст отзыва",
    )

    _ = await service.add_comment(data)

    assert mock_db.add.call_count == 1
    assert mock_db.flush.call_count == 1
    # 2 записи в relationst: sub + subject
    assert mock_db.execute.call_count == 2
    assert mock_db.commit.call_count == 1
