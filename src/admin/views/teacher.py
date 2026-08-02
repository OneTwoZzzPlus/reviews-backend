from typing import ClassVar

from markupsafe import Markup
from sqladmin import action
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.views.base import BaseAdminView
from core.database import async_session_maker
from models.reviews import Teacher
from services.insights import process_selected_teachers_background


class TeacherAdmin(BaseAdminView, model=Teacher):
    name = "Teacher"
    name_plural = "Teachers"
    icon = "fa-solid fa-chalkboard-user"
    page_size = 25
    page_size_options: ClassVar = [25, 50, 100]

    column_list: ClassVar = [
        Teacher.id,
        Teacher.name,
        Teacher.insight,
        Teacher.comments,
        Teacher.subjects,
    ]

    column_searchable_list: ClassVar = [Teacher.name]

    column_sortable_list: ClassVar = [
        Teacher.id,
        Teacher.name,
    ]

    column_formatters: ClassVar = {
        Teacher.summaries: lambda m, _: [str(len(m.summaries))],
        Teacher.comments: lambda m, _: [str(len(m.comments))],
        Teacher.subjects: lambda m, _: (
            m.subjects[:1] + [f"and {len(m.subjects)} more"]
            if len(m.subjects) > 1
            else m.subjects
        ),
        Teacher.insight: lambda m, _: (
            Markup(
                f'<a class="btn btn-sm btn-outline-info" href="/admin/insights/details/{m.insight.id}">'
                f'<i class="fa-solid fa-brain me-1"></i> Insight</a>'
            )
            if m.insight
            else Markup('<span class="badge bg-light text-muted">None</span>')
        ),
    }

    form_columns: ClassVar = [
        "id",
        "name",
        "subjects",
    ]
    form_include_pk = True

    form_ajax_refs: ClassVar = {
        "subjects": {
            "fields": ("title",),
        },
    }

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
            url=request.headers.get("referer", "/admin/teacher/list"),
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
            url=request.headers.get("referer", "/admin/teacher/list"),
            status_code=303,
            background=task,
        )
