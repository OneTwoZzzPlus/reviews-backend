from fastapi import Request
from src.services.reviews import ReviewsService
from src.services.moderator import ModeratorService
from src.services.authp import AuthItmoIdService


moderator_service = None


def get_database(request: Request) -> ReviewsService:
    return request.app.state.database


def get_reviews_service(request: Request) -> ReviewsService:
    return ReviewsService(database=get_database(request))


def get_moderator_service(request: Request) -> ModeratorService:
    return ModeratorService(database=get_database(request))


def get_authp_service(request: Request) -> AuthItmoIdService:
    return AuthItmoIdService()
