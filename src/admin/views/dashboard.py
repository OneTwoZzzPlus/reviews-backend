from typing import ClassVar

from sqladmin import BaseView, expose
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.views.base import touch_data_version
from core.database import async_session_maker
from enums.reviews import SuggestionStatus
from models.content import Suggestion
from services.gsparser import GSParserService


class DashboardAdmin(BaseView):
    name: ClassVar[str] = "Dashboard"
    icon: ClassVar[str] = "fa-solid fa-gauge"
    identity: ClassVar[str] = ""

    @expose("/dashboard", methods=["GET"])
    async def index(self, request: Request):
        """Render dashboard page with system statistics."""
        parsed_count = request.query_params.get("parsed")
        error_msg = request.query_params.get("error")

        async with async_session_maker() as session:
            # Get pending suggestions count
            pending_count = (
                await session.scalar(
                    select(func.count(Suggestion.id)).where(
                        Suggestion.status == SuggestionStatus.delayed
                    )
                )
                or 0
            )

            # Get total suggestions count
            total_count = await session.scalar(select(func.count(Suggestion.id))) or 0

        return await self.templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "pending_count": pending_count,
                "total_count": total_count,
                "parsed_count": parsed_count,
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
