from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.cache import get_data_version


class ETagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Применяем валидацию кеша только к публичным GET-запросам (API)
        # Игнорируем сам интерфейс админки (/admin), чтобы не залочить саму админку
        if request.method == "GET" and not request.url.path.startswith("/admin"):
            current_etag = get_data_version()
            client_etag = request.headers.get("if-none-match")

            # Если версия у клиента совпадает с серверной — сразу отдаём 304 (0 байт)
            if client_etag == current_etag:
                return Response(status_code=304, headers={"ETag": current_etag})

            response = await call_next(request)

            # Для успешных ответов 200 OK проставляем ETag и Cache-Control
            if response.status_code == 200:
                response.headers["ETag"] = current_etag
                # no-cache заставляет браузер всегда делать валидационный запрос (304),
                # а не брать данные совсем вслепую без обращения к серверу
                response.headers["Cache-Control"] = "no-cache"

            return response

        return await call_next(request)
