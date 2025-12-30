from src.models import *


class Service:
    def __init__(self, database):
        self.database = database

    async def search(self, query: str) -> SearchResponse:
        return await self.database.select_search(query)

    async def teacher(self, iid: int) -> TeacherResponse:
        return await self.database.select_teacher(iid)

    async def subject(self, iid: int) -> SubjectResponse:
        return await self.database.select_subject(iid)
