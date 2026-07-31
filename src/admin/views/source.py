from typing import ClassVar

from sqladmin import ModelView

from models.reviews import Source


class SourceAdmin(ModelView, model=Source):
    name = "Source"
    name_plural = "Sources"
    icon = "fa-solid fa-link"
    page_size = 25

    column_list: ClassVar = [Source.id, Source.title, Source.link]
    column_searchable_list: ClassVar = [Source.title]
    column_sortable_list: ClassVar = [Source.id, Source.title]

    form_columns: ClassVar = [Source.title, Source.link]
