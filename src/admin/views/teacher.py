from typing import ClassVar

from sqladmin import ModelView

from models.reviews import Teacher


class TeacherAdmin(ModelView, model=Teacher):
    name = "Teacher"
    name_plural = "Teachers"
    icon = "fa-solid fa-people-group"
    page_size = 25
    page_size_options: ClassVar = [25, 50, 100]

    column_list: ClassVar = [
        Teacher.id,
        Teacher.name,
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
