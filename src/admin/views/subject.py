from typing import ClassVar

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
        Subject.teachers,
    ]

    column_searchable_list: ClassVar = [Subject.title]

    column_sortable_list: ClassVar = [
        Subject.id,
        Subject.title,
    ]

    column_formatters: ClassVar = {
        Subject.teachers: lambda m, _: [f"{len(m.teachers)}"],
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
