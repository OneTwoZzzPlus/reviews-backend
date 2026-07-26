from unittest.mock import AsyncMock

import pytest

from enums import SearchType
from services.reviews import ReviewsService


@pytest.fixture(autouse=True)
def reset_cache():
    ReviewsService._teachers_cache = []
    ReviewsService._subjects_cache = []
    ReviewsService._cache_loaded = False
    yield
    ReviewsService._cache_loaded = False


async def test_search_loads_cache_if_not_loaded(mock_db):
    service = ReviewsService(mock_db)
    service.reload_cache = AsyncMock()

    await service.search("тест", None)
    service.reload_cache.assert_called_once()


async def test_search_empty_query_returns_empty_results(mock_db):
    ReviewsService._cache_loaded = True
    service = ReviewsService(mock_db)

    res = await service.search("", None)
    assert res.results == []


async def test_search_exact_match_and_strainer(mock_db):
    ReviewsService._cache_loaded = True
    ReviewsService._teachers_cache = [{"id": 1, "title": "Иванов Иван"}]
    ReviewsService._subjects_cache = [{"id": 2, "title": "Иван и Математика"}]

    service = ReviewsService(mock_db)

    # Поиск только среди преподавателей
    res = await service.search("иван", SearchType.teacher)
    assert len(res.results) == 1
    assert res.results[0].id == 1
    assert res.results[0].type == SearchType.teacher
