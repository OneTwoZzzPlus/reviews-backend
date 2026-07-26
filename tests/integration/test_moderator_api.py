import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from main import app
from core.auth import token_header, get_isu
from services.moderator import get_moderator_service
from services.reviews import get_reviews_service
from services.gsparser import get_gsparser_service, GSParserService
from enums import SuggestionStatus
from schemas.reviews import (
    SuggestionListResponse,
    SuggestionItem,
    SuggestionResponse,
    InputItem,
    SuggestionCommitResponse,
    SuggestionCancelResponse,
    CommentAddResponse,
    TeacherUpdateResponse,
    SubjectUpdateResponse,
)


@pytest.fixture
def mock_mod_service():
    service = AsyncMock()
    service.have_access.return_value = True
    return service


@pytest.fixture
def mock_reviews_service():
    return AsyncMock()


@pytest.fixture
def mock_gsparser_service():
    return AsyncMock()


@pytest.fixture
async def client(mock_mod_service, mock_reviews_service, mock_gsparser_service):
    app.dependency_overrides[token_header] = lambda: "test-token"
    app.dependency_overrides[get_isu] = lambda: 100001
    app.dependency_overrides[get_moderator_service] = lambda: mock_mod_service
    app.dependency_overrides[get_reviews_service] = lambda: mock_reviews_service
    app.dependency_overrides[get_gsparser_service] = lambda: mock_gsparser_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# GET /mod
# ============================================================================


async def test_moderator_check_access_success(client, mock_mod_service):
    response = await client.get("/mod")

    assert response.status_code == 200
    assert response.json() == {"access": True}


async def test_moderator_check_access_unauthorized(client):
    app.dependency_overrides[get_isu] = lambda: None

    response = await client.get("/mod")
    assert response.status_code == 401


# ============================================================================
# GET /mod/suggestion
# ============================================================================


async def test_suggestion_list_success(client, mock_reviews_service):
    mock_reviews_service.list_suggestion.return_value = SuggestionListResponse(
        items=[
            SuggestionItem(
                id=1,
                status=SuggestionStatus.delayed,
                title="Иванов И.И.",
                source_id=1,
            )
        ]
    )

    response = await client.get("/mod/suggestion")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_suggestion_list_forbidden(client, mock_mod_service):
    mock_mod_service.have_access.return_value = False

    response = await client.get("/mod/suggestion")
    assert response.status_code == 403


# ============================================================================
# GET /mod/suggestion/{iid}
# ============================================================================


async def test_suggestion_get_success(client, mock_reviews_service):
    mock_reviews_service.get_suggestion.return_value = SuggestionResponse(
        id=1,
        status=SuggestionStatus.delayed,
        user_isu=100001,
        moderator_isu=None,
        text="Отличный преподаватель",
        teacher=InputItem(id=1, title="Иванов И.И."),
        subject=InputItem(id=2, title="Математика"),
        subs=[],
        comment_id=None,
    )

    response = await client.get("/mod/suggestion/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


async def test_suggestion_get_not_found(client, mock_reviews_service):
    mock_reviews_service.get_suggestion.return_value = None

    response = await client.get("/mod/suggestion/999")
    assert response.status_code == 404


async def test_suggestion_get_forbidden(client, mock_mod_service):
    mock_mod_service.have_access.return_value = False

    response = await client.get("/mod/suggestion/1")
    assert response.status_code == 403


# ============================================================================
# POST /mod/suggestion/{iid}/commit
# ============================================================================


async def test_suggestion_commit_success(client, mock_reviews_service):
    mock_reviews_service.commit_suggestion.return_value = SuggestionCommitResponse(
        comment_id=10
    )

    payload = {
        "teacher": {"id": 1, "title": "Иванов И.И."},
        "subject": {"id": 2, "title": "Математика"},
        "subs": [],
        "text": "Принятый отзыв",
    }

    response = await client.post("/mod/suggestion/1/commit", json=payload)

    assert response.status_code == 201
    assert response.json() == {"comment_id": 10}


async def test_suggestion_commit_not_found(client, mock_reviews_service):
    mock_reviews_service.commit_suggestion.return_value = None

    payload = {
        "teacher": {"id": 1, "title": "Иванов И.И."},
        "subject": {"id": 2, "title": "Математика"},
        "subs": [],
        "text": "Отзыв",
    }

    response = await client.post("/mod/suggestion/999/commit", json=payload)
    assert response.status_code == 404


async def test_suggestion_commit_forbidden(client, mock_mod_service):
    mock_mod_service.have_access.return_value = False

    payload = {
        "teacher": {"id": 1, "title": "Иванов И.И."},
        "subject": {"id": 2, "title": "Математика"},
        "subs": [],
        "text": "Отзыв",
    }

    response = await client.post("/mod/suggestion/1/commit", json=payload)
    assert response.status_code == 403


# ============================================================================
# POST /mod/suggestion/{iid}/cancel
# ============================================================================


async def test_suggestion_cancel_success(client, mock_reviews_service):
    mock_reviews_service.cancel_suggestion.return_value = SuggestionCancelResponse(
        status=SuggestionStatus.rejected
    )

    response = await client.post(
        "/mod/suggestion/1/cancel", json={"status": "rejected"}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "rejected"}


async def test_suggestion_cancel_not_found(client, mock_reviews_service):
    mock_reviews_service.cancel_suggestion.return_value = None

    response = await client.post(
        "/mod/suggestion/999/cancel", json={"status": "rejected"}
    )
    assert response.status_code == 404


# ============================================================================
# POST /mod/comment
# ============================================================================


async def test_comment_add_success(client, mock_reviews_service):
    mock_reviews_service.add_comment.return_value = CommentAddResponse(id=5)

    payload = {
        "source_id": 1,
        "date": "12:00 01.01.2025",
        "teacher": {"id": 1, "title": "Препод"},
        "subject": {"id": 2, "title": "Предмет"},
        "subs": [],
        "text": "Текст отзыва",
    }

    response = await client.post("/mod/comment", json=payload)

    assert response.status_code == 201
    assert response.json() == {"id": 5}


# ============================================================================
# POST /mod/teacher & POST /mod/subject
# ============================================================================


async def test_teacher_upsert_success(client, mock_reviews_service):
    mock_reviews_service.upsert_teacher.return_value = TeacherUpdateResponse(id=1)

    response = await client.post("/mod/teacher", json={"id": 1, "title": "Иванов И.И."})

    assert response.status_code == 201
    assert response.json() == {"id": 1}


async def test_subject_upsert_success(client, mock_reviews_service):
    mock_reviews_service.upsert_subject.return_value = SubjectUpdateResponse(id=2)

    response = await client.post("/mod/subject", json={"id": 2, "title": "Математика"})

    assert response.status_code == 201
    assert response.json() == {"id": 2}


# ============================================================================
# GET /mod/gsparser
# ============================================================================


async def test_gsparser_success(client, mock_gsparser_service):
    mock_gsparser_service.parse.return_value = 15

    response = await client.get("/mod/gsparser")

    assert response.status_code == 200
    assert response.json() == {"count": 15}


async def test_gsparser_inaccessible(client, mock_gsparser_service):
    mock_gsparser_service.InaccessibleGSheet = GSParserService.InaccessibleGSheet
    mock_gsparser_service.parse.side_effect = GSParserService.InaccessibleGSheet(
        "GSheet error"
    )

    response = await client.get("/mod/gsparser")
    assert response.status_code == 503


async def test_gsparser_invalid(client, mock_gsparser_service):
    mock_gsparser_service.InvalidGSheet = GSParserService.InvalidGSheet
    mock_gsparser_service.parse.side_effect = GSParserService.InvalidGSheet(
        "Invalid table format"
    )

    response = await client.get("/mod/gsparser")
    assert response.status_code == 502
