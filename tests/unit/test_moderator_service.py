import pytest

from services.moderator import ModeratorService


@pytest.fixture(autouse=True)
def clear_moderator_cache():
    """Сбрасываем кэш модераторов перед каждым тестом,
    чтобы тесты не влияли друг на друга.
    """
    ModeratorService._moderators_cache = set()
    yield
    ModeratorService._moderators_cache = set()


# ==================================================
# REFRESH MODERATORS
# ==================================================


async def test_refresh_moderators_success(mock_db):
    """HAPPY
    Успешная обсессия модераторов из БД и загрузка их в кэш
    """
    # Задаем список ISU модераторов, у которых access=True
    expected_isu_list = [100001, 100002, 100003]
    mock_db.return_data(expected_isu_list)

    service = ModeratorService(mock_db)
    await service.refresh_moderators()

    assert mock_db.scalars.call_count == 1
    assert ModeratorService._moderators_cache == set(expected_isu_list)


async def test_refresh_moderators_empty(mock_db):
    """HAPPY (Edge case)
    Обновление кэша, когда в БД нет активных модераторов
    """
    mock_db.return_data(None)

    service = ModeratorService(mock_db)
    await service.refresh_moderators()

    assert mock_db.scalars.call_count == 1
    assert ModeratorService._moderators_cache == set()


# ==================================================
# HAVE ACCESS
# ==================================================


async def test_have_access_when_cache_empty_loads_cache_and_grants_access(mock_db):
    """HAPPY
    При первом вызове have_access кэш пуст -> кэш автоматически
    загружается из БД, и метод возвращает True для разрешенного ISU
    """
    allowed_isu = 123456
    mock_db.return_data([allowed_isu, 654321])

    service = ModeratorService(mock_db)

    # Кэш изначально пуст
    assert len(ModeratorService._moderators_cache) == 0

    has_access = await service.have_access(allowed_isu)

    # Проверяем, что залезли в БД (scalars был вызван)
    assert mock_db.scalars.call_count == 1
    assert has_access is True
    assert allowed_isu in ModeratorService._moderators_cache


async def test_have_access_denied_for_unknown_isu(mock_db):
    """HAPPY
    Возвращает False для ISU, которого нет в списке модераторов
    """
    mock_db.return_data([100001, 100002])

    service = ModeratorService(mock_db)
    unknown_isu = 999999

    has_access = await service.have_access(unknown_isu)

    assert has_access is False


async def test_have_access_uses_cache_without_db_query(mock_db):
    """HAPPY / OPTIMIZATION
    Повторные вызовы have_access используют кэш в памяти и не делают запросов к БД
    """
    ModeratorService._moderators_cache = {111111, 222222}

    service = ModeratorService(mock_db)

    # Запрашиваем доступ для существующего и несуществующего ISU
    access_granted = await service.have_access(111111)
    access_denied = await service.have_access(333333)

    assert access_granted is True
    assert access_denied is False
    # Так как кэш был заполнен, обращения к БД не должно быть!
    assert mock_db.scalars.call_count == 0
