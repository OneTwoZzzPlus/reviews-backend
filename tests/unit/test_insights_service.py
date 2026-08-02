from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai.errors import APIError
from sqlalchemy.exc import SQLAlchemyError

from models.insights import Insights
from models.reviews import Comment, Subject, Teacher
from services.insights import (
    EvaluationParseError,
    GeminiAPIError,
    InsightsDatabaseError,
    InsightsService,
    TeacherNotFoundError,
    process_selected_teachers_background,
    run_bulk_insights_processing,
)
from services.prompt import (
    ConfidenceScore,
    DifficultyScore,
    Evaluation,
    GradingFairnessScore,
    OrganizationScore,
    RatingScore,
    Scores,
    StrictnessScore,
    StudentAttitudeScore,
    TeachingScore,
    WorkloadScore,
)

# ==================================================
# FIXTURES
# ==================================================


@pytest.fixture
def mock_evaluation():
    """Создает валидный объект Evaluation для ответов LLM."""
    return Evaluation(
        summary="Преподаватель отлично объясняет материал и всегда готов помочь.",
        pros=["Понятно объясняет", "Справедливый"],
        cons=["Строгий дедлайн"],
        highlights=["Интересные лекции"],
        scores=Scores(
            teaching=TeachingScore(value="HIGH", reason="Доходчиво подает материал."),
            student_attitude=StudentAttitudeScore(
                value="POSITIVE", reason="Уважительно относится к студентам."
            ),
            organization=OrganizationScore(
                value="GOOD", reason="Четкий график сдачи работ."
            ),
            grading_fairness=GradingFairnessScore(
                value="FAIR", reason="Оценивает исключительно по знаниям."
            ),
            strictness=StrictnessScore(
                value="STRICT", reason="Требует соблюдения сроков."
            ),
            workload=WorkloadScore(value="MODERATE", reason="Объем заданий адекватен."),
            difficulty=DifficultyScore(
                value="MODERATE", reason="Средний уровень сложности."
            ),
        ),
        rating=RatingScore(
            value="POSITIVE", reason="Преобладают положительные отзывы."
        ),
        confidence=ConfidenceScore(
            value="HIGH", reason="Большое количество развернутых отзывов."
        ),
    )


@pytest.fixture
def mock_teacher():
    """Создает тестовую модель преподавателя с одним комментарием."""
    subject = MagicMock(spec=Subject)
    subject.title = "Математический анализ"

    comment = MagicMock(spec=Comment)
    comment.subject = subject
    comment.date = "2024-01-15"
    comment.text = "Прекрасный преподаватель!"

    teacher = MagicMock(spec=Teacher)
    teacher.id = 1
    teacher.name = "Иванов И.И."
    teacher.comments = [comment]
    teacher.insight = None

    return teacher


@pytest.fixture
def insights_service(mock_db):
    """Фикстура сервиса с заглушкой для Gemini Client."""
    with patch("services.insights.genai.Client"):
        service = InsightsService(session=mock_db)
        # Подменяем асинхронный метод обращения к Gemini API
        service.client.aio.models.generate_content = AsyncMock()
        return service


# ==================================================
# UNIT TESTS: InsightsService.process_teacher
# ==================================================


async def test_process_teacher_not_found(insights_service, mock_db):
    """Падает с TeacherNotFoundError, если преподаватель не найден в БД."""
    mock_db.scalar.return_value = None

    with pytest.raises(TeacherNotFoundError):
        await insights_service.process_teacher(teacher_id=999)


async def test_process_teacher_no_comments(insights_service, mock_db, mock_teacher):
    """Пропускает обработку и возвращает False, если у препода нет отзывов."""
    mock_teacher.comments = []
    mock_db.scalar.return_value = mock_teacher

    result = await insights_service.process_teacher(teacher_id=1)

    assert result is False
    insights_service.client.aio.models.generate_content.assert_not_called()


async def test_process_teacher_already_up_to_date(
    insights_service, mock_db, mock_teacher
):
    """Пропускает обработку, если инсайт уже свежий (force=False)."""
    mock_insight = MagicMock(spec=Insights)
    mock_insight.comments_count = 1  # Совпадает с len(mock_teacher.comments)
    mock_teacher.insight = mock_insight
    mock_db.scalar.return_value = mock_teacher

    result = await insights_service.process_teacher(teacher_id=1, force=False)

    assert result is False
    insights_service.client.aio.models.generate_content.assert_not_called()


async def test_process_teacher_force_recalculate(
    insights_service, mock_db, mock_teacher, mock_evaluation
):
    """При force=True пересчитывает инсайт, даже если количество отзывов не изменилось."""
    mock_insight = MagicMock(spec=Insights)
    mock_insight.comments_count = 1
    mock_teacher.insight = mock_insight
    mock_db.scalar.return_value = mock_teacher

    mock_response = MagicMock()
    mock_response.parsed = mock_evaluation
    insights_service.client.aio.models.generate_content.return_value = mock_response

    result = await insights_service.process_teacher(teacher_id=1, force=True)

    assert result is True
    insights_service.client.aio.models.generate_content.assert_called_once()
    mock_db.merge.assert_called_once()
    mock_db.commit.assert_called_once()


async def test_process_teacher_success(
    insights_service, mock_db, mock_teacher, mock_evaluation
):
    """Успешная генерация и сохранение инсайта в БД."""
    mock_db.scalar.return_value = mock_teacher

    mock_response = MagicMock()
    mock_response.parsed = mock_evaluation
    insights_service.client.aio.models.generate_content.return_value = mock_response

    result = await insights_service.process_teacher(teacher_id=1)

    assert result is True
    insights_service.client.aio.models.generate_content.assert_called_once()

    # Проверяем, что объект был передан на сохранение в сессию
    mock_db.merge.assert_called_once()
    saved_insight = mock_db.merge.call_args[0][0]
    assert isinstance(saved_insight, Insights)
    assert saved_insight.id == 1
    assert saved_insight.comments_count == 1
    assert saved_insight.summary == mock_evaluation.summary
    assert saved_insight.rating_value == "POSITIVE"

    mock_db.commit.assert_called_once()


async def test_process_teacher_gemini_api_error(
    insights_service, mock_db, mock_teacher
):
    """Преобразует APIError от библиотеки Gemini в GeminiAPIError."""
    mock_db.scalar.return_value = mock_teacher

    api_error = APIError.__new__(APIError)
    api_error.args = ("Rate limit exceeded",)

    insights_service.client.aio.models.generate_content.side_effect = api_error

    with pytest.raises(GeminiAPIError):
        await insights_service.process_teacher(teacher_id=1)


async def test_process_teacher_validation_error(
    insights_service, mock_db, mock_teacher
):
    """Выбрасывает EvaluationParseError, если ответ от LLM пустой или невалидный."""
    mock_db.scalar.return_value = mock_teacher

    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = None
    insights_service.client.aio.models.generate_content.return_value = mock_response

    with pytest.raises(EvaluationParseError):
        await insights_service.process_teacher(teacher_id=1)


async def test_process_teacher_db_error(
    insights_service, mock_db, mock_teacher, mock_evaluation
):
    """Откатывает транзакцию и выбрасывает InsightsDatabaseError при сбое БД."""
    mock_db.scalar.return_value = mock_teacher

    mock_response = MagicMock()
    mock_response.parsed = mock_evaluation
    insights_service.client.aio.models.generate_content.return_value = mock_response

    mock_db.commit.side_effect = SQLAlchemyError("DB Lock Timeout")

    with pytest.raises(InsightsDatabaseError):
        await insights_service.process_teacher(teacher_id=1)

    mock_db.rollback.assert_called_once()


# ==================================================
# UNIT TESTS: InsightsService.get_teachers_needing_update
# ==================================================


async def test_get_teachers_needing_update(insights_service, mock_db):
    """Проверяет получение списка ID преподавателей, требующих обновления."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [1, 2, 5]
    mock_db.scalars.return_value = mock_scalars

    result = await insights_service.get_teachers_needing_update()

    assert result == [1, 2, 5]
    mock_db.scalars.assert_called_once()


# ==================================================
# UNIT TESTS: Background Tasks & Helpers
# ==================================================


@patch("services.insights.asyncio.sleep", new_callable=AsyncMock)
@patch("services.insights.touch_data_version")
async def test_process_selected_teachers_background(
    mock_touch_data_version, mock_sleep
):
    """Проверяет фоновую обработку списка преподавателей и сброс кэша."""
    session_mock = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__.return_value = session_mock

    with patch.object(
        InsightsService, "process_teacher", new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = True

        await process_selected_teachers_background(
            session_factory=session_factory,
            teacher_ids=[10, 20],
            force=False,
            delay=0.1,
        )

        assert mock_process.call_count == 2
        assert mock_sleep.call_count == 2
        mock_touch_data_version.assert_called_once()


@patch("services.insights.asyncio.sleep", new_callable=AsyncMock)
@patch("services.insights.touch_data_version")
async def test_run_bulk_insights_processing_breaks_on_any_gemini_error(
    mock_touch_data_version,
    mock_sleep,
):
    """
    При возникновении любой GeminiAPIError цикл должен немедленно прерваться,
    не обрабатывая оставшихся учителей и не вызывая дополнительных задержек.
    """
    # Подготовка моков сессии
    session_mock = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__.return_value = session_mock

    # Список учителей для обработки
    teacher_ids = [101, 102, 103]

    with (
        patch.object(
            InsightsService,
            "get_teachers_needing_update",
            new_callable=AsyncMock,
            return_value=teacher_ids,
        ) as mock_get_ids,
        patch.object(
            InsightsService,
            "process_teacher",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        # Первый же вызов process_teacher выбрасывает GeminiAPIError
        mock_process.side_effect = GeminiAPIError("Simulated API error")

        # Запускаем массовую обработку с маленькой задержкой для теста
        await run_bulk_insights_processing(
            session_factory=session_factory,
            delay=0.1,
        )

        # Проверяем, что process_teacher был вызван ровно один раз (для первого учителя)
        assert mock_process.call_count == 1
        mock_process.assert_called_once_with(101, force=False)

        # Проверяем, что asyncio.sleep не вызывался ни разу
        # (потому что мы прервались до await sleep(delay))
        assert mock_sleep.call_count == 0

        # Так как ни один учитель не был успешно обработан, версия данных не обновляется
        mock_touch_data_version.assert_not_called()

        # Убедимся, что get_teachers_needing_update был вызван (это происходит до цикла)
        mock_get_ids.assert_awaited_once()
