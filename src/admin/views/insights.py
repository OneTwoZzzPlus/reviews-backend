from typing import ClassVar

from markupsafe import Markup
from sqladmin import action
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.views.base import BaseAdminView
from core.database import async_session_maker
from enums.insights import ConfidenceScore, RatingScore
from models.insights import Insights
from services.insights import process_selected_teachers_background

RATING_BADGE_ATTRS: dict[str, str] = {
    RatingScore.UNKNOWN: 'class="badge bg-light text-dark border"',
    RatingScore.TERRIBLE: 'class="badge text-white" style="background-color: #5D4037;"',
    RatingScore.NEGATIVE: 'class="badge bg-danger text-white"',
    RatingScore.MIXED: 'class="badge bg-secondary text-white"',
    RatingScore.POSITIVE: 'class="badge bg-success text-white"',
    RatingScore.EXCELLENT: 'class="badge text-dark fw-bold" style="background-color: #FFC107;"',
}

CONFIDENCE_BADGE_ATTRS: dict[str, str] = {
    ConfidenceScore.LOW: 'class="badge bg-danger text-white"',
    ConfidenceScore.MEDIUM: 'class="badge bg-warning text-dark"',
    ConfidenceScore.HIGH: 'class="badge bg-success text-white"',
}

DEFAULT_BADGE_ATTR = 'class="badge bg-secondary text-white"'


def _format_badge(value: str | None, attrs_map: dict[str, str], icon: str) -> str:
    if value is None:
        return "—"
    attrs = attrs_map.get(value, DEFAULT_BADGE_ATTR)
    return Markup(f'<span {attrs}><i class="{icon} me-1"></i>{value}</span>')


class InsightsAdmin(BaseAdminView, model=Insights):
    name = "Insight"
    name_plural = "Insights"
    icon = "fa-solid fa-brain"
    page_size = 25
    page_size_options: ClassVar = [25, 50, 100]

    column_list: ClassVar = [
        Insights.id,
        Insights.teacher,
        Insights.comments_count,
        Insights.rating_value,
        Insights.confidence_value,
    ]

    column_labels: ClassVar = {
        Insights.comments_count: "сomments",
    }

    column_sortable_list: ClassVar = [
        Insights.id,
        Insights.comments_count,
        Insights.rating_value,
        Insights.confidence_value,
    ]

    column_formatters: ClassVar = {
        Insights.rating_value: lambda m, _: _format_badge(
            m.rating_value, RATING_BADGE_ATTRS, "fa-solid fa-star"
        ),
        Insights.confidence_value: lambda m, _: _format_badge(
            m.confidence_value, CONFIDENCE_BADGE_ATTRS, "fa-solid fa-shield-halved"
        ),
    }

    can_create = False
    can_edit = True
    can_delete = True

    @action(
        name="generate_insights",
        label="Smart Generate Insights",
        add_in_detail=True,
        add_in_list=True,
    )
    async def generate_insights(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        teacher_ids = [int(pk) for pk in pks if pk and pk.isdigit()]

        task = None
        if teacher_ids:
            task = BackgroundTask(
                process_selected_teachers_background,
                async_session_maker,
                teacher_ids,
                force=False,
            )

        return RedirectResponse(
            url=request.headers.get("referer", "/admin/insights/list"),
            status_code=303,
            background=task,
        )

    @action(
        name="force_generate_insights",
        label="Force Generate Insights",
        add_in_detail=True,
        add_in_list=True,
    )
    async def force_generate_insights(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        teacher_ids = [int(pk) for pk in pks if pk and pk.isdigit()]

        task = None
        if teacher_ids:
            task = BackgroundTask(
                process_selected_teachers_background,
                async_session_maker,
                teacher_ids,
                force=True,
            )

        return RedirectResponse(
            url=request.headers.get("referer", "/admin/insights/list"),
            status_code=303,
            background=task,
        )
