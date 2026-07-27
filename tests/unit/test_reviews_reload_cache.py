from unittest.mock import MagicMock

import pytest

from services.reviews import ReviewsService


@pytest.fixture(autouse=True)
def reset_cache():
    ReviewsService._teachers_cache = []
    ReviewsService._subjects_cache = []
    ReviewsService._cache_loaded = False
    yield
    ReviewsService._cache_loaded = False


async def test_reload_cache_success(mock_db):
    teachers_data = [(1, "Иванов И.И."), (2, "Петров П.П.")]
    subjects_data = [(10, "Математика"), (20, "Физика")]

    mock_res_t = MagicMock()
    mock_res_t.all.return_value = teachers_data

    mock_res_s = MagicMock()
    mock_res_s.all.return_value = subjects_data

    mock_db.execute.side_effect = [mock_res_t, mock_res_s]

    service = ReviewsService(mock_db)
    await service.reload_cache()

    assert ReviewsService._cache_loaded is True
    assert ReviewsService._teachers_cache == [
        {"title": "Иванов И.И.", "id": 1},
        {"title": "Петров П.П.", "id": 2},
    ]
    assert ReviewsService._subjects_cache == [
        {"title": "Математика", "id": 10},
        {"title": "Физика", "id": 20},
    ]
