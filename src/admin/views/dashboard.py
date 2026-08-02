from typing import ClassVar

from sqladmin import BaseView, expose
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.views.base import touch_data_version
from core.database import async_session_maker
from enums.reviews import SuggestionStatus
from models.content import Suggestion
from models.insights import Insights
from models.reviews import Comment, Source, Subject, Teacher
from services.gsparser import GSParserService
from services.insights import run_bulk_insights_processing


class DashboardAdmin(BaseView):
    name: ClassVar[str] = "Dashboard"
    icon: ClassVar[str] = "fa-solid fa-gauge"
    identity: ClassVar[str] = ""

    @expose("/dashboard", methods=["GET"])
    async def index(self, request: Request):
        """Render dashboard page with system statistics."""
        parsed_count = request.query_params.get("parsed")
        insights_status = request.query_params.get("insights_status")
        error_msg = request.query_params.get("error")

        async with async_session_maker() as session:
            pending_count = (
                await session.scalar(
                    select(func.count(Suggestion.id)).where(
                        Suggestion.status == SuggestionStatus.delayed
                    )
                )
                or 0
            )

            no_insights_count = (
                await session.scalar(
                    select(func.count(Teacher.id))
                    .outerjoin(Teacher.insight)
                    .where(Insights.id == None)
                )
                or 0
            )

            total_comments = await session.scalar(select(func.count(Comment.id))) or 0
            total_teachers = await session.scalar(select(func.count(Teacher.id))) or 0
            total_subjects = await session.scalar(select(func.count(Subject.id))) or 0
            total_sources = await session.scalar(select(func.count(Source.id))) or 0

        return await self.templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "pending_count": pending_count,
                "no_insights_count": no_insights_count,
                "total_comments": total_comments,
                "total_teachers": total_teachers,
                "total_subjects": total_subjects,
                "total_sources": total_sources,
                "parsed_count": parsed_count,
                "insights_status": insights_status,
                "error_msg": error_msg,
            },
        )

    @expose("/dashboard/run-gsparser", methods=["POST"])
    async def run_gsparser(self, request: Request):
        """Trigger GSParser to fetch new suggestions from Google Sheets."""
        try:
            async with async_session_maker() as session:
                parser = GSParserService(session)
                count = await parser.parse()

            if count > 0:
                touch_data_version()

            return RedirectResponse(
                url=f"/admin/dashboard?parsed={count}",
                status_code=303,
            )
        except (GSParserService.MainException, SQLAlchemyError) as e:
            return RedirectResponse(
                url=f"/admin/dashboard?error={e!s}",
                status_code=303,
            )

    @expose("/dashboard/run-insights", methods=["POST"])
    async def run_insights(self, request: Request):
        """Trigger bulk AI Insights processing in background."""
        try:
            task = BackgroundTask(run_bulk_insights_processing, async_session_maker)
            return RedirectResponse(
                url="/admin/dashboard?insights_status=started",
                status_code=303,
                background=task,
            )
        except Exception as e:  # noqa: BLE001
            return RedirectResponse(
                url=f"/admin/dashboard?error={e!s}",
                status_code=303,
            )
