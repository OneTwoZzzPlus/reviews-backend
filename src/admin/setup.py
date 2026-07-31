from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqladmin import Admin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from admin.auth import AdminAuth, hash_password
from admin.views.comment import CommentAdmin
from admin.views.moderator import ModeratorAdmin
from admin.views.source import SourceAdmin
from admin.views.subject import SubjectAdmin
from admin.views.summary import SummaryAdmin
from admin.views.teacher import TeacherAdmin
from core.config import settings
from core.database import async_session_maker
from models.content import Moderator


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="Admin",
        base_url="/admin",
    )

    @app.get("/admin", include_in_schema=False)
    async def admin_redirect():
        return RedirectResponse("/admin/")

    admin.add_view(SubjectAdmin)
    admin.add_view(TeacherAdmin)
    admin.add_view(SummaryAdmin)
    admin.add_view(CommentAdmin)
    admin.add_view(SourceAdmin)
    admin.add_view(ModeratorAdmin)

    return admin


async def seed_initial_admin() -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(Moderator).limit(1))
        exists = result.scalar_one_or_none()

        if not exists:
            admin_isu = 100000
            admin_password = settings.MASTER_PASSWORD

            initial_admin = Moderator(
                isu=admin_isu,
                name="admin",
                access=True,
                password_hash=hash_password(admin_password),
            )
            session.add(initial_admin)
            await session.commit()
