from unittest.mock import MagicMock

import pytest

from schemas.insights import (
    Confidence,
    Rating,
    Scores,
)
from schemas.reviews import (
    TeacherResponse,
)
from services.reviews import ReviewsService


@pytest.mark.asyncio
async def test_teacher_not_found(mock_db):
    mock_db.scalar.return_value = None
    service = ReviewsService(mock_db)

    res = await service.teacher(1)
    assert res is None
    mock_db.scalar.assert_called_once()


@pytest.mark.asyncio
async def test_teacher_found_without_insight(mock_db):
    mock_teacher = MagicMock()
    mock_teacher.id = 1
    mock_teacher.name = "Иванов И.И."
    mock_teacher.insight = None
    mock_teacher.summaries = []
    mock_teacher.comments = []

    mock_db.scalar.return_value = mock_teacher
    service = ReviewsService(mock_db)

    res = await service.teacher(1)

    assert isinstance(res, TeacherResponse)
    assert res.id == 1
    assert res.name == "Иванов И.И."
    assert res.insights is None
    assert res.summaries == []
    assert res.comments == []


@pytest.mark.asyncio
async def test_teacher_found_with_full_data(mock_db):
    mock_insight = MagicMock()
    mock_insight.summary = "Хороший преподаватель"
    mock_insight.pros = ["понятно объясняет"]
    mock_insight.cons = ["много домашки"]
    mock_insight.highlights = ["доброжелателен"]

    # Все значения заменены на строки из соответствующих enum
    mock_insight.rating_value = "POSITIVE"
    mock_insight.rating_reason = "в целом отлично"
    mock_insight.confidence_value = "HIGH"
    mock_insight.confidence_reason = "много отзывов"
    mock_insight.teaching_value = "VERY_HIGH"
    mock_insight.teaching_reason = "отличная подача"
    mock_insight.student_attitude_value = "POSITIVE"
    mock_insight.student_attitude_reason = "внимателен"
    mock_insight.organization_value = "AVERAGE"
    mock_insight.organization_reason = "иногда путается"
    mock_insight.grading_fairness_value = "FAIR"
    mock_insight.grading_fairness_reason = "объективен"
    mock_insight.strictness_value = "MODERATE"
    mock_insight.strictness_reason = "средняя строгость"
    mock_insight.workload_value = "HEAVY"
    mock_insight.workload_reason = "много заданий"
    mock_insight.difficulty_value = "HARD"
    mock_insight.difficulty_reason = "сложный материал"

    mock_summary1 = MagicMock(title="Лекции", value="интересные")
    mock_summary2 = MagicMock(title="Практика", value="полезная")

    mock_comment = MagicMock()
    mock_comment.id = 101
    mock_comment.date = "2025-01-15"
    mock_comment.text = "Отличный преподаватель!"
    mock_comment.source = MagicMock(title="ВКонтакте", link="https://vk.com/...")
    mock_comment.subject = MagicMock(title="Алгебра")

    mock_teacher = MagicMock()
    mock_teacher.id = 1
    mock_teacher.name = "Иванов И.И."
    mock_teacher.insight = mock_insight
    mock_teacher.summaries = [mock_summary1, mock_summary2]
    mock_teacher.comments = [mock_comment]

    mock_db.scalar.return_value = mock_teacher
    service = ReviewsService(mock_db)

    res = await service.teacher(1)

    assert isinstance(res, TeacherResponse)
    assert res.id == 1
    assert res.name == "Иванов И.И."

    assert res.insights is not None
    assert res.insights.summary == "Хороший преподаватель"
    assert res.insights.pros == ["понятно объясняет"]
    assert res.insights.cons == ["много домашки"]
    assert res.insights.highlights == ["доброжелателен"]

    assert isinstance(res.insights.rating, Rating)
    assert res.insights.rating.value == "POSITIVE"
    assert res.insights.rating.reason == "в целом отлично"

    assert isinstance(res.insights.confidence, Confidence)
    assert res.insights.confidence.value == "HIGH"
    assert res.insights.confidence.reason == "много отзывов"

    assert isinstance(res.insights.scores, Scores)
    assert res.insights.scores.teaching.value == "VERY_HIGH"
    assert res.insights.scores.teaching.reason == "отличная подача"
    assert res.insights.scores.student_attitude.value == "POSITIVE"
    assert res.insights.scores.organization.value == "AVERAGE"
    assert res.insights.scores.grading_fairness.value == "FAIR"
    assert res.insights.scores.strictness.value == "MODERATE"
    assert res.insights.scores.workload.value == "HEAVY"
    assert res.insights.scores.difficulty.value == "HARD"

    assert len(res.summaries) == 2
    assert res.summaries[0].title == "Лекции"
    assert res.summaries[0].value == "интересные"

    assert len(res.comments) == 1
    comment = res.comments[0]
    assert comment.id == 101
    assert comment.text == "Отличный преподаватель!"
    assert comment.source.title == "ВКонтакте"
    assert comment.source.link == "https://vk.com/..."
    assert comment.subject.title == "Алгебра"
