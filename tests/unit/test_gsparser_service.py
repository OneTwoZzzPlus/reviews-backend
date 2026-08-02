from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from enums.reviews import SuggestionStatus
from models.content import Processed, Suggestion
from services.gsparser import (
    GSParserService,
    get_gsparser_service,
)


@pytest.fixture
def parser_service(mock_db):
    """Фикстура сервиса парсера с мокнутой БД."""
    return GSParserService(session=mock_db)


# ==================================================
# UNIT TESTS: Вспомогательные методы (Pure Functions)
# ==================================================


def test_convert_datetime_valid(parser_service):
    """Корректно преобразует строку даты и времени."""
    raw_date = "15.10.2024 14:30:45"
    expected = "14:30 15.10.2024"

    result = parser_service.convert_datetime(raw_date)

    assert result == expected


def test_convert_datetime_invalid(parser_service):
    """Возвращает значения по умолчанию при невалидной строке даты."""
    invalid_inputs = ["invalid", "", "15.10.2024", "15.10 14:30:45"]

    for val in invalid_inputs:
        assert parser_service.convert_datetime(val) == "00:00 00.00.2023"


def test_generate_row_id_full_row(parser_service):
    """Генерирует воспроизводимый MD5 хэш из строки данных."""
    row = ["15.10.2024 14:30:00", "Иванов И.И.", "Физика", "Отличный препод"]

    row_id_1 = parser_service.generate_row_id(row)
    row_id_2 = parser_service.generate_row_id(row)

    assert isinstance(row_id_1, str)
    assert len(row_id_1) == 32  # Стандартная длина MD5 хэша
    assert row_id_1 == row_id_2


def test_generate_row_id_incomplete_row(parser_service):
    """Безопасно генерирует хэш, если в строке меньше колонок, чем ожидается."""
    short_row = ["15.10.2024 14:30:00"]  # Указана только дата

    row_id = parser_service.generate_row_id(short_row)

    assert isinstance(row_id, str)
    assert len(row_id) == 32


# ==================================================
# UNIT TESTS: load_sheet (Сетевой слой / httpx)
# ==================================================


@patch("httpx.AsyncClient.get")
async def test_load_sheet_success(mock_get, parser_service):
    """Успешно загружает и парсит CSV таблицы."""
    csv_content = '"Дата","Преподаватель","Предмет","Отзыв"\n"01.01.2024 10:00:00","Петров","Алгебра","Тест"'

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.text = csv_content
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    rows = await parser_service.load_sheet()

    assert len(rows) == 2
    assert rows[1] == ["01.01.2024 10:00:00", "Петров", "Алгебра", "Тест"]


@patch("httpx.AsyncClient.get")
async def test_load_sheet_empty_data(mock_get, parser_service):
    """Выбрасывает InvalidGSheet, если CSV пустой."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.text = ""
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with pytest.raises(GSParserService.InvalidGSheet):
        await parser_service.load_sheet()


@patch("httpx.AsyncClient.get")
async def test_load_sheet_http_status_error(mock_get, parser_service):
    """Выбрасывает InaccessibleGSheet при 4xx/5xx ошибках HTTP."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    error = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=mock_response
    )
    mock_get.side_effect = error

    with pytest.raises(GSParserService.InaccessibleGSheet) as exc_info:
        await parser_service.load_sheet()

    assert "(404) Not Found" in str(exc_info.value)


@patch("httpx.AsyncClient.get")
async def test_load_sheet_request_error(mock_get, parser_service):
    """Выбрасывает InaccessibleGSheet при таймауте или сетевом сбое."""
    mock_get.side_effect = httpx.RequestError("Connection timeout", request=MagicMock())

    with pytest.raises(GSParserService.InaccessibleGSheet) as exc_info:
        await parser_service.load_sheet()

    assert "Request failed: Connection timeout" in str(exc_info.value)


# ==================================================
# UNIT TESTS: parse (Основной бизнес-процесс)
# ==================================================


async def test_parse_saves_new_records(parser_service, mock_db):
    """Успешно добавляет новые записи и делает commit."""
    rows = [
        ["01.01.2024 12:00:00", "Сидоров С.С.", "Матанализ", "Хороший преподоб"],
        ["02.01.2024 13:00:00", "Иванов И.И.", "Физика", "Классный"],
    ]
    parser_service.load_sheet = AsyncMock(return_value=rows)

    # В БД пока нет обработанных ID
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_db.scalars.return_value = mock_scalars

    added_count = await parser_service.parse()

    assert added_count == 2
    # Для каждого ряда добавляется Suggestion и Processed (всего 4 вызова db.add)
    assert mock_db.add.call_count == 4
    mock_db.commit.assert_called_once()

    # Проверяем правильность первого добавленного Suggestion
    first_add_call = mock_db.add.call_args_list[0][0][0]
    assert isinstance(first_add_call, Suggestion)
    assert first_add_call.teacher_title == "Сидоров С.С."
    assert first_add_call.subject_title == "Матанализ"
    assert first_add_call.status == SuggestionStatus.delayed
    assert first_add_call.source_id == 2

    # Проверяем правильность первого добавленного Processed
    second_add_call = mock_db.add.call_args_list[1][0][0]
    assert isinstance(second_add_call, Processed)
    assert second_add_call.id == parser_service.generate_row_id(rows[0])


async def test_parse_skips_already_processed_and_empty(parser_service, mock_db):
    """Пропускает пустые и ранее обработанные строки."""
    already_processed_row = ["01.01.2024 12:00:00", "Учитель 1", "Предмет 1", "Отзыв 1"]
    processed_id = parser_service.generate_row_id(already_processed_row)

    new_row = ["02.01.2024 13:00:00", "Учитель 2", "Предмет 2", "Отзыв 2"]

    rows = [
        ["", "", "", ""],  # Пустая строка
        already_processed_row,  # Уже обработанная
        new_row,  # Новая строка
    ]
    parser_service.load_sheet = AsyncMock(return_value=rows)

    # Задаем, что processed_id уже существует в БД
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [processed_id]
    mock_db.scalars.return_value = mock_scalars

    added_count = await parser_service.parse()

    assert added_count == 1
    assert mock_db.add.call_count == 2  # 1 Suggestion + 1 Processed
    mock_db.commit.assert_called_once()


async def test_parse_no_new_rows_does_not_commit(parser_service, mock_db):
    """Если новых строк нет, commit не вызывается."""
    rows = [["01.01.2024 12:00:00", "Учитель 1", "Предмет 1", "Отзыв 1"]]
    parser_service.load_sheet = AsyncMock(return_value=rows)

    processed_id = parser_service.generate_row_id(rows[0])
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [processed_id]
    mock_db.scalars.return_value = mock_scalars

    added_count = await parser_service.parse()

    assert added_count == 0
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


# ==================================================
# UNIT TESTS: FastAPI Dependency Generator
# ==================================================


async def test_get_gsparser_service_dependency(mock_db):
    """Проверяет корректность генерации зависимости get_gsparser_service."""
    gen = get_gsparser_service(session=mock_db)
    service = await anext(gen)

    assert isinstance(service, GSParserService)
    assert service.session == mock_db

    with pytest.raises(StopAsyncIteration):
        await anext(gen)
