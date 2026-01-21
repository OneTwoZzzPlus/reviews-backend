from src.models import *


class ReviewsService:
    def __init__(self, database):
        self.database = database

    async def search(self, query: str, strainer: str | None) -> SearchResponse:
        return await self.database.select_search(query, strainer)

    async def teacher(self, iid: int, isu: int | None = None) -> TeacherResponse:
        return await self.database.select_teacher(iid, 0 if isu is None else isu)

    async def subject(self, iid: int, isu: int | None = None) -> SubjectResponse:
        return await self.database.select_subject(iid, 0 if isu is None else isu)

    async def teacher_rate(self, isu: int, iid: int, rating: int) -> TeacherRateResponse:
        return await self.database.upsert_teacher_rating(isu, iid, rating)

    async def comment_vote(self, isu: int, iid: int, karma: int) -> CommentKarmaResponse:
        return await self.database.upsert_comment_karma(isu, iid, karma)
