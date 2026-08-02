from typing import ClassVar

from admin.views.base import BaseAdminView
from models.reviews import Comment


class CommentAdmin(BaseAdminView, model=Comment):
    name = "Comment"
    name_plural = "Comments"
    icon = "fa-solid fa-comments"
    page_size = 25

    column_list: ClassVar = [
        Comment.id,
        Comment.date,
        Comment.source,
        Comment.teacher,
        Comment.subject,
        Comment.text,
    ]
    column_searchable_list: ClassVar = [
        "teacher.name",
        "subject.title",
    ]
    column_sortable_list: ClassVar = [
        Comment.id,
        Comment.date,
        Comment.source,
        Comment.teacher,
        Comment.subject,
    ]

    column_formatters: ClassVar = {
        Comment.text: lambda m, _: m.text[:25] + "..." if len(m.text) > 25 else m.text,
    }

    form_columns: ClassVar = [
        "date",
        "text",
        "teacher",
        "subject",
        "source",
    ]

    # Быстрый поиск для всех связанных объектов
    form_ajax_refs: ClassVar = {
        "teacher": {"fields": ("name",)},
        "subject": {"fields": ("title",)},
        "source": {"fields": ("title",)},
    }
