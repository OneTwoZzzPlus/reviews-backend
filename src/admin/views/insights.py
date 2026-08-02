from typing import ClassVar

from markupsafe import Markup

from admin.views.base import BaseAdminView
from models.insights import Insights


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

    column_sortable_list: ClassVar = [
        Insights.id,
        Insights.comments_count,
        Insights.rating_value,
        Insights.confidence_value,
    ]

    column_formatters: ClassVar = {
        Insights.rating_value: lambda m, _: (
            Markup(
                f'<span class="badge bg-warning text-dark">'
                f'<i class="fa-solid fa-star me-1"></i>{m.rating_value}'
                f"</span>"
            )
            if m.rating_value is not None
            else "—"
        ),
        Insights.confidence_value: lambda m, _: (
            Markup(
                f'<span class="badge bg-info">'
                f'<i class="fa-solid fa-shield-halved me-1"></i>{m.confidence_value}'
                f"</span>"
            )
            if m.confidence_value is not None
            else "—"
        ),
    }

    can_create = False
    can_edit = True
    can_delete = True
