from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqladmin import Admin
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from admin.auth import AdminAuth, hash_password
from admin.views.comment import CommentAdmin
from admin.views.dashboard import DashboardAdmin
from admin.views.insights import InsightsAdmin
from admin.views.moderator import ModeratorAdmin
from admin.views.source import SourceAdmin
from admin.views.subject import SubjectAdmin
from admin.views.suggestion import SuggestionAdmin
from admin.views.summary import SummaryAdmin
from admin.views.teacher import TeacherAdmin
from core.config import settings
from core.database import async_session_maker
from models.content import Moderator

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class AdminRedirectMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] in ("/admin", "/admin/"):
            response = RedirectResponse(url="/admin/dashboard", status_code=302)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    app.add_middleware(AdminRedirectMiddleware)

    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="Admin",
        base_url="/admin",
        templates_dir=str(TEMPLATES_DIR),
    )

    @app.get("/admin", include_in_schema=False)
    async def admin_redirect():
        return RedirectResponse(url="/admin/", status_code=302)

    admin.add_view(DashboardAdmin)
    admin.add_view(SuggestionAdmin)
    admin.add_view(SubjectAdmin)
    admin.add_view(TeacherAdmin)
    admin.add_view(InsightsAdmin)
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
