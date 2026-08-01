from typing import ClassVar

from markupsafe import Markup
from sqladmin import action, expose
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from starlette.requests import Request
from starlette.responses import RedirectResponse

from admin.views.base import BaseAdminView, touch_data_version
from core.database import async_session_maker
from enums import SuggestionStatus
from models.content import Suggestion
from models.reviews import Comment, RelationST, Subject, Teacher


class SuggestionAdmin(BaseAdminView, model=Suggestion):
    name: ClassVar[str] = "Suggestion"
    name_plural: ClassVar[str] = "Suggestions"
    icon: ClassVar[str] = "fa-solid fa-lightbulb"

    can_create: ClassVar[bool] = False
    can_edit: ClassVar[bool] = False
    can_delete: ClassVar[bool] = True

    column_list: ClassVar[list[str]] = [
        "id",
        "status",
        "date",
        "teacher_title",
        "subject_title",
        "text",
    ]
    column_searchable_list: ClassVar[list[str]] = [
        "teacher_title",
        "subject_title",
    ]
    column_sortable_list: ClassVar[list[str]] = ["id", "status"]

    column_formatters: ClassVar[dict] = {
        "id": lambda model, attr: Markup(
            f'<a class="btn btn-sm btn-outline-primary" href="/admin/suggestion/moderate/{model.id}">'
            f'<i class="fa-solid fa-gavel"></i> #{model.id}</a>'
        )
    }

    def list_query(self, request: Request):
        return super().list_query(request).where(Suggestion.status == SuggestionStatus.delayed)

    def count_query(self, request: Request):
        return super().count_query(request).where(Suggestion.status == SuggestionStatus.delayed)

    @action(
        name="moderate_selected",
        label="Moderation",
        add_in_detail=True,
        add_in_list=True,
    )
    async def moderate_selected(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        if pks and pks[0]:
            return RedirectResponse(
                url=f"/admin/suggestion/moderate/{pks[0]}", status_code=302
            )
        return RedirectResponse(
            url=request.headers.get("referer", "/admin/suggestion/list"),
            status_code=302,
        )

    @action(name="mark_rejected", label="Reject", add_in_list=True)
    async def mark_rejected(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        updated = False
        async with async_session_maker() as session:
            for pk in pks:
                if pk:
                    s = await session.get(Suggestion, int(pk))
                    if s and s.status == SuggestionStatus.delayed:
                        s.status = SuggestionStatus.rejected
                        updated = True
            await session.commit()

        if updated:
            touch_data_version()

        return RedirectResponse(
            url=request.headers.get("referer", "/admin/suggestion/list"),
            status_code=303,
        )

    @action(name="mark_spam", label="Spam", add_in_list=True)
    async def mark_spam(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        updated = False
        async with async_session_maker() as session:
            for pk in pks:
                if pk:
                    s = await session.get(Suggestion, int(pk))
                    if s and s.status == SuggestionStatus.delayed:
                        s.status = SuggestionStatus.spam
                        updated = True
            await session.commit()

        if updated:
            touch_data_version()

        return RedirectResponse(
            url=request.headers.get("referer", "/admin/suggestion/list"),
            status_code=303,
        )

    @expose("/moderate/{pk}", methods=["GET"])
    async def moderate_page(self, request: Request):
        pk = int(request.path_params["pk"])

        async with async_session_maker() as session:
            suggestion = await session.get(Suggestion, pk)
            if not suggestion or suggestion.status != SuggestionStatus.delayed:
                return RedirectResponse("/admin/suggestion/list", status_code=302)

            teachers_res = await session.execute(select(Teacher))
            teachers = teachers_res.scalars().all()

            subjects_res = await session.execute(select(Subject))
            subjects = subjects_res.scalars().all()

            suggested_subs = []
            if suggestion.subs_title:
                titles = suggestion.subs_title.split(";")
                ids = suggestion.subs_id.split(";") if suggestion.subs_id else []
                for idx, t in enumerate(titles):
                    sub_id = ids[idx] if idx < len(ids) and ids[idx] else None
                    suggested_subs.append({"id": sub_id, "title": t})

            return await self.templates.TemplateResponse(
                request,
                "suggestion.html",
                {
                    "suggestion": suggestion,
                    "suggested_subs": suggested_subs,
                    "teachers": teachers,
                    "subjects": subjects,
                },
            )

    @expose("/moderate/{pk}/commit", methods=["POST"])
    async def commit_review(self, request: Request):
        pk = int(request.path_params["pk"])
        form = await request.form()
        action_type = form.get("action_type")

        async with async_session_maker() as session:
            suggestion = await session.get(Suggestion, pk)
            if not suggestion or suggestion.status != SuggestionStatus.delayed:
                return RedirectResponse("/admin/suggestion/list", status_code=303)

            moderator_isu = request.state.user.isu if hasattr(request.state, "user") else None

            if action_type == "accept":
                cleaned_text = str(form.get("cleaned_text", "")).strip()
                teacher_id = int(form.get("teacher_id", 0))
                subject_id = int(form.get("subject_id", 0))

                raw_subs = form.getlist("sub_ids")
                sub_ids = [int(x) for x in raw_subs if x and str(x).isdigit()]

                new_comment = Comment(
                    text=cleaned_text,
                    teacher_id=teacher_id,
                    subject_id=subject_id,
                    date=suggestion.date,
                    source_id=suggestion.source_id,
                )
                session.add(new_comment)
                await session.flush()

                target_subjects = set([subject_id] + sub_ids)
                for s_id in target_subjects:
                    if s_id:
                        rel_stmt = (
                            pg_insert(RelationST)
                            .values(teacher_id=teacher_id, subject_id=s_id)
                            .on_conflict_do_nothing()
                        )
                        await session.execute(rel_stmt)

                suggestion.status = SuggestionStatus.accepted
                suggestion.comment_id = new_comment.id
                if moderator_isu:
                    suggestion.moderator_isu = moderator_isu

            elif action_type == "reject":
                suggestion.status = SuggestionStatus.rejected
                if moderator_isu:
                    suggestion.moderator_isu = moderator_isu

            elif action_type == "spam":
                suggestion.status = SuggestionStatus.spam
                if moderator_isu:
                    suggestion.moderator_isu = moderator_isu

            await session.commit()

        touch_data_version()

        return RedirectResponse("/admin/suggestion/list", status_code=303)