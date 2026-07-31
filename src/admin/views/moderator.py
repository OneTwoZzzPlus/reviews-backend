from typing import Any, ClassVar

from fastapi import HTTPException
from sqladmin import ModelView
from starlette.requests import Request
from wtforms import Form, PasswordField

from admin.auth import hash_password, verify_password
from core.config import settings
from models.content import Moderator


class ModeratorAdmin(ModelView, model=Moderator):
    name = "Moderator"
    name_plural = "Moderators"
    icon = "fa-solid fa-user-shield"

    form_include_pk = True

    column_list: ClassVar = [
        Moderator.isu,
        Moderator.name,
        Moderator.access,
    ]

    column_searchable_list: ClassVar = ["name", "isu"]
    column_sortable_list: ClassVar = ["isu", "name", "access"]

    form_columns: ClassVar = ["isu", "name", "access"]

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        form_class = await super().scaffold_form(rules)
        form_class.new_password = PasswordField("New Password")
        form_class.old_password = PasswordField("Current Password")
        form_class.master_password = PasswordField("Master Password")
        return form_class

    async def on_model_change(
        self, data: dict[str, Any], model: Any, is_created: bool, request: Request
    ) -> None:
        new_password = data.pop("new_password", None)
        old_password = data.pop("old_password", None)
        master_password = data.pop("master_password", None)

        if new_password:
            if is_created:
                if master_password != settings.MASTER_PASSWORD:
                    raise HTTPException(
                        status_code=400,
                        detail="Master Password required!",
                    )
            else:
                is_old_valid = (
                    old_password
                    and model.password_hash
                    and verify_password(old_password, model.password_hash)
                )
                is_master_valid = (
                    master_password and master_password == settings.MASTER_PASSWORD
                )

                if not (is_old_valid or is_master_valid):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid credentials!",
                    )

            data["password_hash"] = hash_password(new_password)
