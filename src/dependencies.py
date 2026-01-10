from fastapi import Request
from src.services.reviews import Service


def get_database(request: Request) -> Service:
    return request.app.state.database


def get_service(request: Request) -> Service:
    return Service(database=get_database(request))
