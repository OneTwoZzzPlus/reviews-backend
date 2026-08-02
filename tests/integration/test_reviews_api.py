from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from schemas.insights import Confidence, InsightsEssential, Rating
from schemas.reviews import (
    RegistryResponse,
    SearchItem,
    SearchResponse,
    SubjectResponse,
    SuggestionResponse,
    TeacherResponse,
)
from services.reviews import get_reviews_service


@pytest.fixture
def mock_reviews_service():
    service = AsyncMock()
    return service


@pytest.fixture
async def client(mock_reviews_service):
    app.dependency_overrides[get_reviews_service] = lambda: mock_reviews_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# GET /search
# ============================================================================


async def test_search_success(client, mock_reviews_service):
    mock_reviews_service.search.return_value = SearchResponse(
        results=[SearchItem(id=1, title="Иванов И.И.", type="teacher")]
    )

    response = await client.get("/search?query=иван")

    assert response.status_code == 200
    assert response.json() == {
        "results": [{"id": 1, "title": "Иванов И.И.", "type": "teacher"}]
    }


async def test_search_validation_error_short_query(client):
    response = await client.get("/search?query=a")
    assert response.status_code == 422


async def test_search_not_found(client, mock_reviews_service):
    mock_reviews_service.search.return_value = None

    response = await client.get("/search?query=несуществующий")
    assert response.status_code == 404


# ============================================================================
# GET /teacher/{iid}
# ============================================================================


async def test_get_teacher_success(client, mock_reviews_service):
    mock_reviews_service.teacher.return_value = TeacherResponse(
        id=1, name="Петров П.П.", summaries=[], comments=[]
    )

    response = await client.get("/teacher/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Петров П.П."


async def test_get_teacher_not_found(client, mock_reviews_service):
    mock_reviews_service.teacher.return_value = None

    response = await client.get("/teacher/999")
    assert response.status_code == 404


# ============================================================================
# GET /subject/{iid}
# ============================================================================


async def test_get_subject_success(client, mock_reviews_service):
    mock_reviews_service.subject.return_value = SubjectResponse(
        id=10, title="Математика", teachers=[]
    )

    response = await client.get("/subject/10")

    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert response.json()["title"] == "Математика"


async def test_get_subject_not_found(client, mock_reviews_service):
    mock_reviews_service.subject.return_value = None

    response = await client.get("/subject/999")
    assert response.status_code == 404


# ============================================================================
# POST /suggestion
# ============================================================================


async def test_suggestion_success(client, mock_reviews_service):
    mock_reviews_service.add_suggestion.return_value = SuggestionResponse(id=42)

    payload = {
        "teacher": {"id": 1, "title": None},
        "subject": {"id": 2, "title": None},
        "subs": [{"id": 3, "title": None}],
        "text": "Хороший преподаватель",
    }

    response = await client.post("/suggestion", json=payload)

    assert response.status_code == 202
    assert response.json() == {"id": 42}


async def test_suggestion_invalid_teacher(client):
    payload = {
        "teacher": {"id": None, "title": None},
        "subject": {"id": 2, "title": "Физика"},
        "subs": [],
        "text": "Текст",
    }

    response = await client.post("/suggestion", json=payload)
    assert response.status_code == 400


async def test_suggestion_invalid_subject(client):
    payload = {
        "teacher": {"id": 1, "title": "Учитель"},
        "subject": {"id": None, "title": None},
        "subs": [],
        "text": "Текст",
    }

    response = await client.post("/suggestion", json=payload)
    assert response.status_code == 400


async def test_suggestion_invalid_subs(client):
    payload = {
        "teacher": {"id": 1, "title": "Учитель"},
        "subject": {"id": 2, "title": "Физика"},
        "subs": [{"id": None, "title": None}],
        "text": "Текст",
    }

    response = await client.post("/suggestion", json=payload)
    assert response.status_code == 400


# ============================================================================
# GET /registry
# ============================================================================


async def test_get_registry_success(client, mock_reviews_service):
    """
    Успешное получение реестра преподавателей с инсайтами.
    """
    # Создаём мок-ответ RegistryResponse
    mock_registry = RegistryResponse(
        original={"Иванов И.И.": 1, "Петров П.П.": 2},
        normalized={"иванови.и.": 1, "петровп.п.": 2},
        insights={
            1: InsightsEssential(
                summary="Хороший преподаватель",
                rating=Rating(value="POSITIVE", reason="отлично"),
                confidence=Confidence(value="HIGH", reason="много отзывов"),
            ),
            2: InsightsEssential(
                summary="Строгий, но справедливый",
                rating=Rating(value="EXCELLENT", reason="очень хорошо"),
                confidence=Confidence(value="MEDIUM", reason="несколько отзывов"),
            ),
        },
    )

    mock_reviews_service.registry.return_value = mock_registry

    response = await client.get("/registry")

    assert response.status_code == 200
    data = response.json()

    # Проверяем структуру ответа
    assert "original" in data
    assert "normalized" in data
    assert "insights" in data

    assert data["original"] == {"Иванов И.И.": 1, "Петров П.П.": 2}
    assert data["normalized"] == {"иванови.и.": 1, "петровп.п.": 2}

    # Проверяем инсайты
    insights = data["insights"]
    assert "1" in insights
    assert "2" in insights
    assert insights["1"]["summary"] == "Хороший преподаватель"
    assert insights["1"]["rating"]["value"] == "POSITIVE"
    assert insights["1"]["confidence"]["value"] == "HIGH"


async def test_get_registry_empty(client, mock_reviews_service):
    """
    Реестр может вернуть пустые словари (если нет преподавателей с инсайтами).
    """
    mock_registry = RegistryResponse(
        original={},
        normalized={},
        insights={},
    )

    mock_reviews_service.registry.return_value = mock_registry

    response = await client.get("/registry")

    assert response.status_code == 200
    data = response.json()
    assert data["original"] == {}
    assert data["normalized"] == {}
    assert data["insights"] == {}
