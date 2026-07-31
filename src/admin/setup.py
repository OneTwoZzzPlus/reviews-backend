from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.middleware.sessions import SessionMiddleware

from admin.auth import AdminAuth
from admin.views.teacher import TeacherAdmin
from core.config import settings


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
    )

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

    admin.add_view(TeacherAdmin)

    return admin
