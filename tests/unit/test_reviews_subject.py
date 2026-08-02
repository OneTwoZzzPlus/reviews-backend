from unittest.mock import MagicMock

import pytest

from schemas.insights import Confidence, InsightsShort, Rating
from schemas.reviews import SubjectResponse, TeacherShort
from services.reviews import ReviewsService


@pytest.mark.asyncio
async def test_subject_not_found(mock_db):
    mock_db.scalar.return_value = None
    service = ReviewsService(mock_db)

    res = await service.subject(1)
    assert res is None
    mock_db.scalar.assert_called_once()


@pytest.mark.asyncio
async def test_subject_found_with_teachers(mock_db):
    mock_insight = MagicMock()
    mock_insight.summary = "Отличный лектор"
    mock_insight.pros = ["доступно"]
    mock_insight.cons = ["быстро"]
    mock_insight.highlights = ["шутки"]
    mock_insight.rating_value = "EXCELLENT"
    mock_insight.rating_reason = "очень хорошо"
    mock_insight.confidence_value = "HIGH"
    mock_insight.confidence_reason = "много оценок"

    mock_comment = MagicMock()
    mock_comment.text = "Очень понятно объясняет!"

    mock_teacher = MagicMock()
    mock_teacher.id = 5
    mock_teacher.name = "Петров П.П."
    mock_teacher.insight = mock_insight
    mock_teacher.comments = [mock_comment]

    mock_subject = MagicMock()
    mock_subject.id = 10
    mock_subject.title = "Алгебра"
    mock_subject.teachers = [mock_teacher]

    mock_db.scalar.return_value = mock_subject
    service = ReviewsService(mock_db)

    res = await service.subject(10)

    assert isinstance(res, SubjectResponse)
    assert res.id == 10
    assert res.title == "Алгебра"
    assert len(res.teachers) == 1

    teacher_short = res.teachers[0]
    assert isinstance(teacher_short, TeacherShort)
    assert teacher_short.id == 5
    assert teacher_short.name == "Петров П.П."
    assert teacher_short.alt == "Очень понятно объясняет!"  # <30 слов → без многоточия

    assert teacher_short.insights is not None
    assert isinstance(teacher_short.insights, InsightsShort)
    assert teacher_short.insights.summary == "Отличный лектор"
    assert teacher_short.insights.pros == ["доступно"]
    assert teacher_short.insights.cons == ["быстро"]
    assert teacher_short.insights.highlights == ["шутки"]

    assert isinstance(teacher_short.insights.rating, Rating)
    assert teacher_short.insights.rating.value == "EXCELLENT"
    assert teacher_short.insights.rating.reason == "очень хорошо"

    assert isinstance(teacher_short.insights.confidence, Confidence)
    assert teacher_short.insights.confidence.value == "HIGH"
    assert teacher_short.insights.confidence.reason == "много оценок"


@pytest.mark.asyncio
async def test_subject_found_with_teacher_no_insight(mock_db):
    mock_teacher = MagicMock()
    mock_teacher.id = 7
    mock_teacher.name = "Сидоров С.С."
    mock_teacher.insight = None
    mock_teacher.comments = [MagicMock(text="Хороший преподаватель")]

    mock_subject = MagicMock()
    mock_subject.id = 20
    mock_subject.title = "Математика"
    mock_subject.teachers = [mock_teacher]

    mock_db.scalar.return_value = mock_subject
    service = ReviewsService(mock_db)

    res = await service.subject(20)

    assert len(res.teachers) == 1
    teacher = res.teachers[0]
    assert teacher.insights is None
    assert teacher.alt == "Хороший преподаватель"


@pytest.mark.asyncio
async def test_subject_found_with_no_comments(mock_db):
    mock_teacher = MagicMock()
    mock_teacher.id = 8
    mock_teacher.name = "Кузнецов К.К."
    mock_teacher.insight = None
    mock_teacher.comments = []

    mock_subject = MagicMock()
    mock_subject.id = 30
    mock_subject.title = "Физика"
    mock_subject.teachers = [mock_teacher]

    mock_db.scalar.return_value = mock_subject
    service = ReviewsService(mock_db)

    res = await service.subject(30)
    teacher = res.teachers[0]
    assert teacher.alt is None
