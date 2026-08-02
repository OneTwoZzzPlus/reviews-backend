from unittest.mock import MagicMock

import pytest

from core.cache import get_data_version, touch_data_version
from services.reviews import ReviewsService


@pytest.fixture(autouse=True)
def reset_cache():
    """Сбрасываем кеш перед каждым тестом"""
    ReviewsService._version = None
    ReviewsService._teachers_cache = []
    ReviewsService._subjects_cache = []
    ReviewsService._registry = None
    yield
    ReviewsService._version = None
    ReviewsService._teachers_cache = []
    ReviewsService._subjects_cache = []
    ReviewsService._registry = None


async def test_reload_cache_success(mock_db):
    """
    Успешная загрузка кеша: teachers, subjects и registry.
    """
    teachers_data = [(1, "Иванов И.И."), (2, "Петров П.П.")]
    mock_teachers = MagicMock()
    mock_teachers.all.return_value = teachers_data

    subjects_data = [(10, "Математика"), (20, "Физика")]
    mock_subjects = MagicMock()
    mock_subjects.all.return_value = subjects_data

    # Создаём teacher'ов отдельно, чтобы name был строкой
    teacher1 = MagicMock()
    teacher1.id = 1
    teacher1.name = "Иванов И.И."

    teacher2 = MagicMock()
    teacher2.id = 2
    teacher2.name = "Петров П.П."

    mock_insight1 = MagicMock()
    mock_insight1.teacher = teacher1
    mock_insight1.summary = "Хороший преподаватель"
    mock_insight1.rating_value = "POSITIVE"
    mock_insight1.rating_reason = "отлично"
    mock_insight1.confidence_value = "HIGH"
    mock_insight1.confidence_reason = "много отзывов"

    mock_insight2 = MagicMock()
    mock_insight2.teacher = teacher2
    mock_insight2.summary = "Строгий, но справедливый"
    mock_insight2.rating_value = "EXCELLENT"
    mock_insight2.rating_reason = "очень хорошо"
    mock_insight2.confidence_value = "MEDIUM"
    mock_insight2.confidence_reason = "несколько отзывов"

    mock_insights_result = MagicMock()
    mock_insights_result.scalars.return_value = [mock_insight1, mock_insight2]

    mock_db.execute.side_effect = [mock_teachers, mock_subjects, mock_insights_result]

    service = ReviewsService(mock_db)
    await service.reload_cache()

    assert ReviewsService._version == get_data_version()
    assert ReviewsService._teachers_cache == [
        {"title": "Иванов И.И.", "id": 1},
        {"title": "Петров П.П.", "id": 2},
    ]
    assert ReviewsService._subjects_cache == [
        {"title": "Математика", "id": 10},
        {"title": "Физика", "id": 20},
    ]

    registry = ReviewsService._registry
    assert registry is not None
    assert registry.original == {
        "Иванов И.И.": 1,
        "Петров П.П.": 2,
    }
    assert registry.normalized == {
        "иванови.и.": 1,
        "петровп.п.": 2,
    }
    assert len(registry.insights) == 2
    assert registry.insights[1].summary == "Хороший преподаватель"
    assert registry.insights[2].summary == "Строгий, но справедливый"


async def test_reload_cache_no_reload_when_version_same(mock_db):
    """При повторном вызове с той же версией запросы к БД не выполняются."""
    teachers_data = [(1, "Тест")]
    mock_teachers = MagicMock()
    mock_teachers.all.return_value = teachers_data

    subjects_data = [(10, "Тест")]
    mock_subjects = MagicMock()
    mock_subjects.all.return_value = subjects_data

    teacher = MagicMock()
    teacher.id = 1
    teacher.name = "Тест"

    mock_insight = MagicMock()
    mock_insight.teacher = teacher
    mock_insight.summary = "Сводка"
    mock_insight.rating_value = "POSITIVE"
    mock_insight.rating_reason = "хорошо"
    mock_insight.confidence_value = "HIGH"
    mock_insight.confidence_reason = "много"

    mock_insights_result = MagicMock()
    mock_insights_result.scalars.return_value = [mock_insight]

    mock_db.execute.side_effect = [mock_teachers, mock_subjects, mock_insights_result]

    service = ReviewsService(mock_db)
    await service.reload_cache()
    assert mock_db.execute.call_count == 3

    mock_db.execute.reset_mock()
    await service.reload_cache()
    mock_db.execute.assert_not_called()


async def test_reload_cache_reload_when_version_changed(mock_db):
    """При изменении версии (touch_data_version) кеш перезагружается."""
    # Первая загрузка
    teachers_data1 = [(1, "Иванов")]
    mock_teachers1 = MagicMock()
    mock_teachers1.all.return_value = teachers_data1

    subjects_data1 = [(10, "Математика")]
    mock_subjects1 = MagicMock()
    mock_subjects1.all.return_value = subjects_data1

    teacher1 = MagicMock()
    teacher1.id = 1
    teacher1.name = "Иванов"

    mock_insight1 = MagicMock()
    mock_insight1.teacher = teacher1
    mock_insight1.summary = "Старый"
    mock_insight1.rating_value = "POSITIVE"
    mock_insight1.rating_reason = "ok"
    mock_insight1.confidence_value = "HIGH"
    mock_insight1.confidence_reason = "много"

    mock_insights_result1 = MagicMock()
    mock_insights_result1.scalars.return_value = [mock_insight1]

    mock_db.execute.side_effect = [
        mock_teachers1,
        mock_subjects1,
        mock_insights_result1,
    ]

    service = ReviewsService(mock_db)
    await service.reload_cache()
    initial_version = ReviewsService._version

    touch_data_version()
    new_version = get_data_version()
    assert new_version != initial_version

    teachers_data2 = [(2, "Петров")]
    mock_teachers2 = MagicMock()
    mock_teachers2.all.return_value = teachers_data2

    subjects_data2 = [(20, "Физика")]
    mock_subjects2 = MagicMock()
    mock_subjects2.all.return_value = subjects_data2

    teacher2 = MagicMock()
    teacher2.id = 2
    teacher2.name = "Петров"

    mock_insight2 = MagicMock()
    mock_insight2.teacher = teacher2
    mock_insight2.summary = "Новый"
    mock_insight2.rating_value = "EXCELLENT"
    mock_insight2.rating_reason = "отлично"
    mock_insight2.confidence_value = "MEDIUM"
    mock_insight2.confidence_reason = "средне"

    mock_insights_result2 = MagicMock()
    mock_insights_result2.scalars.return_value = [mock_insight2]

    mock_db.execute.side_effect = [
        mock_teachers2,
        mock_subjects2,
        mock_insights_result2,
    ]

    await service.reload_cache()

    assert ReviewsService._version == new_version
    assert ReviewsService._teachers_cache == [{"title": "Петров", "id": 2}]
    assert ReviewsService._subjects_cache == [{"title": "Физика", "id": 20}]
    assert ReviewsService._registry.original == {"Петров": 2}
    assert ReviewsService._registry.insights[2].summary == "Новый"
