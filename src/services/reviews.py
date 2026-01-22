from src.models import *


def get_current_time():
    from datetime import datetime, timezone, timedelta
    utc_plus_3 = timezone(timedelta(hours=3))
    current_time = datetime.now(timezone.utc).astimezone(utc_plus_3)
    return current_time.strftime("%H:%M %d:%m:%Y")


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

    async def add_suggestion(self, isu: int | None, data: SuggestionAddRequest) -> SuggestionAddResponse:
        return SuggestionAddResponse(id=await self.database.insert_suggestion(isu, data))

    async def list_suggestion(self, delayed=True, accepted=False, rejected=False) -> SuggestionListResponse:
        return await self.database.select_suggestions(delayed, accepted, rejected)

    async def get_suggestion(self, iid: int) -> SuggestionResponse:
        return await self.database.select_suggestion(iid)

    async def commit_suggestion(self, isu: int, iid: int, body: SuggestionCommitRequest) -> SuggestionCommitResponse:
        return await self.database.commit_suggestion(isu, iid, body, get_current_time())

    async def cancel_suggestion(self, isu: int, iid: int, body: SuggestionCancelRequest) -> SuggestionCancelResponse:
        return await self.database.update_suggestion_status(isu, iid, body.status)


