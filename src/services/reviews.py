import re
from rapidfuzz import fuzz

from src.models import *


def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = text.replace("ё", "е")
    text = re.sub(r'(.)\1+', r'\1', text)
    text = re.sub(r"[^а-яa-z0-9\s]", "", text)
    text = " ".join(text.split())

    return text


def get_current_time():
    from datetime import datetime, timezone, timedelta
    utc_plus_3 = timezone(timedelta(hours=3))
    current_time = datetime.now(timezone.utc).astimezone(utc_plus_3)
    return current_time.strftime("%H:%M %d.%m.%Y")


class ReviewsService:
    def __init__(self, database):
        self.database = database

    async def search(self, query: str, strainer: str | None) -> SearchResponse:
        normalized_query = normalize(query)
        if not normalized_query:
            return SearchResponse(results=[])

        cache = {
            SearchType.teacher: self.database.teachers,
            SearchType.subject: self.database.subjects
        }

        categories = [strainer] if strainer else [SearchType.teacher, SearchType.subject]
        raw_results = []

        for cat in categories:
            data_source = cache.get(cat, [])
            for item in data_source:
                original_title = item["title"]
                target_text = normalize(original_title)

                score = 0
                priority = 3

                if normalized_query in target_text:
                    score = 100
                    priority = 1 if target_text.startswith(normalized_query) else 2
                else:
                    score = fuzz.partial_ratio(normalized_query, target_text)
                    priority = 3

                threshold = 75 if priority < 3 else 85

                if score >= threshold:
                    raw_results.append({
                        "id": item["id"],
                        "title": original_title,
                        "type": cat,
                        "score": score,
                        "priority": priority
                    })

        raw_results.sort(key=lambda x: (
            x["priority"],
            -x["score"],
            x["title"].split()[0]
        ))

        return SearchResponse(results=[
            SearchItem(
                id=res["id"],
                title=res["title"],
                type=res["type"]
            ) for res in raw_results[:20]
        ])

    async def teacher(self, iid: int, isu: int | None = None) -> TeacherResponse:
        return await self.database.select_teacher(iid, 0 if isu is None else isu)

    async def subject(self, iid: int, isu: int | None = None) -> SubjectResponse:
        return await self.database.select_subject(iid, 0 if isu is None else isu)

    async def teacher_rate(self, isu: int, iid: int, rating: int) -> TeacherRateResponse:
        return await self.database.upsert_teacher_rating(isu, iid, rating)

    async def comment_vote(self, isu: int, iid: int, karma: int) -> CommentKarmaResponse:
        return await self.database.upsert_comment_karma(isu, iid, karma)

    async def add_suggestion(self, isu: int | None, data: SuggestionAddRequest) -> SuggestionAddResponse:
        return SuggestionAddResponse(id=await self.database.insert_suggestion(isu, data, get_current_time()))

    async def list_suggestion(self, delayed=True, accepted=False, rejected=False) -> SuggestionListResponse:
        return await self.database.select_suggestions(delayed, accepted, rejected)

    async def get_suggestion(self, iid: int) -> SuggestionResponse:
        return await self.database.select_suggestion(iid)

    async def commit_suggestion(self, isu: int, iid: int, body: SuggestionCommitRequest) -> SuggestionCommitResponse:
        return await self.database.commit_suggestion(isu, iid, body)

    async def cancel_suggestion(self, isu: int, iid: int, body: SuggestionCancelRequest) -> SuggestionCancelResponse:
        return await self.database.update_suggestion_status(isu, iid, body.status)

    async def upsert_teacher(self, data: TeacherUpdateRequest) -> TeacherUpdateResponse:
        return await self.database.upsert_teacher(data)

    async def upsert_subject(self, data: SubjectUpdateRequest) -> SubjectUpdateResponse:
        return await self.database.upsert_subject(data)

    async def add_comment(self, data: CommentAddRequest) -> CommentAddResponse:
        return await self.database.insert_comment(data)
