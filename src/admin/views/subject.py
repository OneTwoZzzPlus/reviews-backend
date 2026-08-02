from typing import ClassVar

from sqlalchemy.orm import selectinload
from starlette.requests import Request

from admin.views.base import BaseAdminView
from models.reviews import Subject


class SubjectAdmin(BaseAdminView, model=Subject):
    name = "Subject"
    name_plural = "Subjects"
    icon = "fa-solid fa-book"
    page_size = 25
    page_size_options: ClassVar = [25, 50, 100]

    column_list: ClassVar = [
        Subject.id,
        Subject.title,
        "teachers_count",
    ]

    column_labels: ClassVar = {
        "teachers_count": "teachers",
    }

    def list_query(self, request: Request):
        return super().list_query(request).options(selectinload(Subject.teachers))

    column_searchable_list: ClassVar = [Subject.title]

    column_sortable_list: ClassVar = [
        Subject.id,
        Subject.title,
    ]

    column_formatters: ClassVar = {
        "teachers_count": lambda m, _: len(m.teachers) if m.teachers else 0,
    }

    form_columns: ClassVar = [
        Subject.title,
        Subject.teachers,
    ]

    form_ajax_refs: ClassVar = {
        "teachers": {
            "fields": ("name",),
        },
    }
