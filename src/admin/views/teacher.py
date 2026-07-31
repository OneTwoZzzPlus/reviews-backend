from typing import ClassVar

from sqladmin import ModelView

from models.reviews import Teacher


class TeacherAdmin(ModelView, model=Teacher):
    name = "Преподаватель"
    name_plural = "Преподаватели"
    icon = "fa-solid fs--chalkboard-user"
    page_size = 25
    page_size_options: ClassVar = [25, 50, 100]

    column_list: ClassVar = [
        Teacher.id,
        Teacher.name,
        Teacher.rating,
        Teacher.subjects,
        Teacher.summaries,
    ]

    column_searchable_list: ClassVar = [Teacher.name]

    column_sortable_list: ClassVar = [
        Teacher.id,
        Teacher.name,
        Teacher.rating,
    ]

    column_formatters: ClassVar = {
        Teacher.subjects: lambda m, _: (
            m.subjects[:1] + ["S"] * (len(m.subjects) - 1)
            if len(m.subjects) > 1
            else m.subjects
        ),
        Teacher.summaries: lambda m, _: (
            ["SUM"] * len(m.summaries) if len(m.summaries) > 1 else m.summaries
        ),
    }

    form_columns: ClassVar = [
        "name",
        "subjects",
    ]

    form_ajax_refs: ClassVar = {
        "subjects": {
            "fields": ("title",),
        },
    }
