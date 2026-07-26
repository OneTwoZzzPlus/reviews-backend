import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from main import app
from services.reviews import get_reviews_service
from core.auth import token_header, get_isu
from schemas.reviews import (
    SearchResponse,
    SearchItem,
    TeacherResponse,
    SubjectResponse,
    TeacherRateResponse,
    CommentKarmaResponse,
    SuggestionAddResponse,
)


@pytest.fixture
def mock_reviews_service():
    service = AsyncMock()
    return service


@pytest.fixture
async def client(mock_reviews_service):
    # Обходим проверку токена и подменяем получение ISU и сервиса
    app.dependency_overrides[token_header] = lambda: "test-token"
    app.dependency_overrides[get_isu] = lambda: 100001
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
        id=1, name="Петров П.П.", rating=4.5, summaries=[], comments=[]
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
# POST /teacher/{iid}/rate
# ============================================================================


async def test_teacher_rate_success(client, mock_reviews_service):
    mock_reviews_service.teacher_rate.return_value = TeacherRateResponse(
        rating=4.8, user_rating=5
    )

    response = await client.post("/teacher/1/rate", json={"user_rating": 5})

    assert response.status_code == 200
    assert response.json() == {"rating": 4.8, "user_rating": 5}


async def test_teacher_rate_unauthorized(client):
    app.dependency_overrides[get_isu] = lambda: None

    response = await client.post("/teacher/1/rate", json={"user_rating": 5})
    assert response.status_code == 401


async def test_teacher_rate_not_found(client, mock_reviews_service):
    mock_reviews_service.teacher_rate.return_value = None

    response = await client.post("/teacher/999/rate", json={"user_rating": 5})
    assert response.status_code == 404


# ============================================================================
# POST /comment/{iid}/vote
# ============================================================================


async def test_comment_vote_success(client, mock_reviews_service):
    mock_reviews_service.comment_vote.return_value = CommentKarmaResponse(
        karma=12, user_karma=1
    )

    response = await client.post("/comment/5/vote", json={"user_karma": 1})

    assert response.status_code == 200
    assert response.json() == {"karma": 12, "user_karma": 1}


async def test_comment_vote_unauthorized(client):
    app.dependency_overrides[get_isu] = lambda: None

    response = await client.post("/comment/5/vote", json={"user_karma": 1})
    assert response.status_code == 401


async def test_comment_vote_not_found(client, mock_reviews_service):
    mock_reviews_service.comment_vote.return_value = None

    response = await client.post("/comment/999/vote", json={"user_karma": 1})
    assert response.status_code == 404


# ============================================================================
# POST /suggestion
# ============================================================================


async def test_suggestion_success(client, mock_reviews_service):
    mock_reviews_service.add_suggestion.return_value = SuggestionAddResponse(id=42)

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
