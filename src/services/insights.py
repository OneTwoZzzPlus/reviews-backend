import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import Depends
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from core.cache import touch_data_version
from core.config import settings
from core.database import AsyncSession, get_database
from models.insights import Insights
from models.reviews import Comment, Teacher
from services.prompt import SYSTEM_PROMPT, Evaluation

logger = logging.getLogger(__name__)


class InsightsServiceError(Exception):
    pass


class GeminiAPIError(InsightsServiceError):
    pass


class EvaluationParseError(InsightsServiceError):
    pass


class InsightsDatabaseError(InsightsServiceError):
    pass


class TeacherNotFoundError(InsightsServiceError):
    pass


class InsightsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = genai.Client(api_key=settings.INSIGHTS_API_KEY)

    @staticmethod
    def _map_evaluation_to_insight(
        teacher_id: int, comments_count: int, eval_data: Evaluation
    ) -> Insights:
        return Insights(
            id=teacher_id,
            comments_count=comments_count,
            summary=eval_data.summary,
            pros=eval_data.pros,
            cons=eval_data.cons,
            highlights=eval_data.highlights,
            teaching_value=eval_data.scores.teaching.value,
            teaching_reason=eval_data.scores.teaching.reason,
            student_attitude_value=eval_data.scores.student_attitude.value,
            student_attitude_reason=eval_data.scores.student_attitude.reason,
            organization_value=eval_data.scores.organization.value,
            organization_reason=eval_data.scores.organization.reason,
            grading_fairness_value=eval_data.scores.grading_fairness.value,
            grading_fairness_reason=eval_data.scores.grading_fairness.reason,
            strictness_value=eval_data.scores.strictness.value,
            strictness_reason=eval_data.scores.strictness.reason,
            workload_value=eval_data.scores.workload.value,
            workload_reason=eval_data.scores.workload.reason,
            difficulty_value=eval_data.scores.difficulty.value,
            difficulty_reason=eval_data.scores.difficulty.reason,
            rating_value=eval_data.rating.value,
            rating_reason=eval_data.rating.reason,
            confidence_value=eval_data.confidence.value,
            confidence_reason=eval_data.confidence.reason,
        )

    @staticmethod
    def _get_teacher_prompt(teacher: Teacher) -> str:
        comments = "\n\n---\n\n".join(
            [
                f"Предмет: {c.subject.title}\nДата: {c.date}\nОтзыв: {c.text}"
                for c in teacher.comments
            ]
        )
        return f"Преподаватель: {teacher.name}\n\nОтзывы:\n\n{comments}"

    async def process_teacher(self, teacher_id: int, force: bool = False) -> bool:
        stmt = (
            select(Teacher)
            .options(
                selectinload(Teacher.insight),
                selectinload(Teacher.comments).joinedload(Comment.subject),
            )
            .where(Teacher.id == teacher_id)
        )
        teacher = await self.session.scalar(stmt)
        if not teacher:
            raise TeacherNotFoundError(f"Teacher {teacher_id} not found")

        comments_count = len(teacher.comments)

        if comments_count == 0:
            logger.info(f"Teacher {teacher_id} has no comments. Skipping.")
            return False

        if (
            not force
            and teacher.insight
            and teacher.insight.comments_count == comments_count
        ):
            logger.info(f"Teacher {teacher_id} already have insights. Skipping.")
            return False

        prompt = self._get_teacher_prompt(teacher)

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=Evaluation,
                ),
            )
        except APIError as e:
            logger.error(f"Gemini API returned error for teacher {teacher_id}: {e}")
            raise GeminiAPIError(f"Failed to fetch insights from LLM: {e}") from e

        try:
            if response.parsed:
                eval_data: Evaluation = response.parsed
            elif response.text:
                eval_data = Evaluation.model_validate_json(response.text)
            else:
                raise ValueError("Empty response text received from LLM")
        except (ValidationError, ValueError) as e:
            logger.error(
                f"Validation failed for teacher {teacher_id}.\n"
                f"Raw response: {getattr(response, 'text', None)}\nError: {e}"
            )
            raise EvaluationParseError(f"LLM output failed validation: {e}") from e

        try:
            insight_data = self._map_evaluation_to_insight(
                teacher_id, comments_count, eval_data
            )
            await self.session.merge(insight_data)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error saving insight for teacher {teacher_id}: {e}")
            raise InsightsDatabaseError(f"Failed to commit insight to DB: {e}") from e

        return True

    async def get_teachers_needing_update(self) -> list[int]:
        stmt = (
            select(Teacher.id)
            .outerjoin(Teacher.insight)
            .outerjoin(Teacher.comments)
            .group_by(Teacher.id, Insights.comments_count)
            .having(
                (Teacher.insight == None)
                | (func.count(Comment.id) != Insights.comments_count)
            )
        )
        result = await self.session.scalars(stmt)
        return result.all()


async def process_selected_teachers_background(
    session_factory, teacher_ids: list[int], force: bool = False, delay: float = 4.5
):
    logger.info(
        f"Starting background insights generation for {len(teacher_ids)} teachers (force={force})."
    )

    processed_count = 0

    for t_id in teacher_ids:
        async with session_factory() as session:
            service = InsightsService(session)
            try:
                was_processed = await service.process_teacher(t_id, force=force)
                await session.commit()
                if was_processed:
                    processed_count += 1
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error generating insight for teacher {t_id}: {e}")

        await asyncio.sleep(delay)

    if processed_count > 0:
        touch_data_version()

    logger.info(f"Finished processing insights for {len(teacher_ids)} teachers.")


async def run_bulk_insights_processing(session_factory, delay: float = 4.5):
    async with session_factory() as session:
        service = InsightsService(session)
        teacher_ids = await service.get_teachers_needing_update()

    logger.info(f"Starting bulk processing for {len(teacher_ids)} teachers.")

    processed = 0
    errors = 0

    for teacher_id in teacher_ids:
        async with session_factory() as session:
            service = InsightsService(session)
            try:
                was_processed = await service.process_teacher(teacher_id, force=False)
                if was_processed:
                    processed += 1
            except GeminiAPIError as e:
                logger.warning(
                    f"Rate limit or API error for teacher {teacher_id}: {e}. Waiting 10s..."
                )
                await asyncio.sleep(10)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to process teacher {teacher_id}: {e}")
                errors += 1

        await asyncio.sleep(delay)

    if processed > 0:
        touch_data_version()

    logger.info(f"Bulk processing finished. Processed: {processed}, Errors: {errors}")


async def get_reviews_service(
    session: AsyncSession = Depends(get_database),
) -> AsyncGenerator[InsightsService, None]:
    yield InsightsService(session=session)
