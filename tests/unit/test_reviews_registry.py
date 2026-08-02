from unittest.mock import MagicMock

import pytest

from core.cache import get_data_version
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


async def test_registry_returns_cached_data(mock_db):
    """Метод registry вызывает reload_cache и возвращает кешированный RegistryResponse."""
    teachers_data = [(1, "Иванов И.И.")]
    mock_teachers = MagicMock()
    mock_teachers.all.return_value = teachers_data

    subjects_data = [(10, "Математика")]
    mock_subjects = MagicMock()
    mock_subjects.all.return_value = subjects_data

    teacher = MagicMock()
    teacher.id = 1
    teacher.name = "Иванов И.И."

    mock_insight = MagicMock()
    mock_insight.teacher = teacher
    mock_insight.summary = "Тест"
    mock_insight.rating_value = "POSITIVE"
    mock_insight.rating_reason = "ok"
    mock_insight.confidence_value = "HIGH"
    mock_insight.confidence_reason = "много"

    mock_insights_result = MagicMock()
    mock_insights_result.scalars.return_value = [mock_insight]

    mock_db.execute.side_effect = [mock_teachers, mock_subjects, mock_insights_result]

    service = ReviewsService(mock_db)
    registry = await service.registry()

    assert registry is not None
    assert registry.original == {"Иванов И.И.": 1}
    assert registry.normalized == {"иванови.и.": 1}
    assert len(registry.insights) == 1
    assert registry.insights[1].summary == "Тест"
    assert ReviewsService._registry is registry
    assert ReviewsService._version == get_data_version()


async def test_registry_skips_insights_without_teacher(mock_db):
    """Инсайты без привязанного учителя игнорируются."""
    teachers_data = [(1, "Иванов")]
    mock_teachers = MagicMock()
    mock_teachers.all.return_value = teachers_data

    subjects_data = [(10, "Математика")]
    mock_subjects = MagicMock()
    mock_subjects.all.return_value = subjects_data

    teacher = MagicMock()
    teacher.id = 1
    teacher.name = "Иванов"

    mock_insight1 = MagicMock()
    mock_insight1.teacher = teacher
    mock_insight1.summary = "Есть учитель"
    mock_insight1.rating_value = "POSITIVE"
    mock_insight1.rating_reason = "ok"
    mock_insight1.confidence_value = "HIGH"
    mock_insight1.confidence_reason = "много"

    mock_insight2 = MagicMock()
    mock_insight2.teacher = None
    mock_insight2.summary = "Без учителя"

    mock_insights_result = MagicMock()
    mock_insights_result.scalars.return_value = [mock_insight1, mock_insight2]

    mock_db.execute.side_effect = [mock_teachers, mock_subjects, mock_insights_result]

    service = ReviewsService(mock_db)
    registry = await service.registry()

    assert len(registry.insights) == 1
    assert 1 in registry.insights
    assert registry.insights[1].summary == "Есть учитель"
    assert 2 not in registry.insights


async def test_registry_normalization_consistency(mock_db):
    """Проверка, что нормализация имён в registry работает единообразно."""
    teachers_data = [(1, "Иванов И. И."), (2, "петров   п.п.")]
    mock_teachers = MagicMock()
    mock_teachers.all.return_value = teachers_data

    subjects_data = [(10, "Математика")]
    mock_subjects = MagicMock()
    mock_subjects.all.return_value = subjects_data

    teacher1 = MagicMock()
    teacher1.id = 1
    teacher1.name = "Иванов И. И."

    teacher2 = MagicMock()
    teacher2.id = 2
    teacher2.name = "петров   п.п."

    mock_insight1 = MagicMock()
    mock_insight1.teacher = teacher1
    mock_insight1.summary = "Первый"
    mock_insight1.rating_value = "POSITIVE"
    mock_insight1.rating_reason = "ok"
    mock_insight1.confidence_value = "HIGH"
    mock_insight1.confidence_reason = "много"

    mock_insight2 = MagicMock()
    mock_insight2.teacher = teacher2
    mock_insight2.summary = "Второй"
    mock_insight2.rating_value = "EXCELLENT"
    mock_insight2.rating_reason = "отлично"
    mock_insight2.confidence_value = "MEDIUM"
    mock_insight2.confidence_reason = "средне"

    mock_insights_result = MagicMock()
    mock_insights_result.scalars.return_value = [mock_insight1, mock_insight2]

    mock_db.execute.side_effect = [mock_teachers, mock_subjects, mock_insights_result]

    service = ReviewsService(mock_db)
    registry = await service.registry()

    assert registry.normalized == {
        "иванови.и.": 1,
        "петровп.п.": 2,
    }
