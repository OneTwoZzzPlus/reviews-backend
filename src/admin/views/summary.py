from typing import ClassVar

from sqladmin import ModelView

from models.reviews import Summary


class SummaryAdmin(ModelView, model=Summary):
    name = "Summary"
    name_plural = "Summaries"
    icon = "fa-solid fa-tags"
    page_size = 25

    column_list: ClassVar = [
        Summary.id,
        Summary.teacher,
        Summary.title,
        Summary.value,
    ]

    column_searchable_list: ClassVar = [Summary.title]
    column_sortable_list: ClassVar = [Summary.id, Summary.title]

    form_columns: ClassVar = [Summary.teacher, Summary.title, Summary.value]

    form_ajax_refs: ClassVar = {
        "teacher": {
            "fields": ("name",),
        },
    }
