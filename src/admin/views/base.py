from typing import Any

from sqladmin import ModelView
from starlette.requests import Request

from core.cache import touch_data_version


class BaseAdminView(ModelView):
    """Базовый класс для всех моделей в SQLAdmin."""

    async def on_model_change(
        self, data: dict[str, Any], model: Any, is_created: bool, request: Request
    ) -> None:
        touch_data_version()

    async def on_model_delete(self, model: Any, request: Request) -> None:
        touch_data_version()
