from rapidfuzz import process, fuzz

from src.models import *


def get_current_time():
    from datetime import datetime, timezone, timedelta
    utc_plus_3 = timezone(timedelta(hours=3))
    current_time = datetime.now(timezone.utc).astimezone(utc_plus_3)
    return current_time.strftime("%H:%M %d.%m.%Y")


class ReviewsService:
    def __init__(self, database):
        self.database = database

    async def search(self, query: str, strainer: str | None) -> SearchResponse:
        cache = {
            SearchType.teacher: self.database.teachers,
            SearchType.subject: self.database.subjects
        }
        results = []

        categories = [strainer] if strainer else [SearchType.teacher, SearchType.subject]
        for cat in categories:

            data_source = cache.get(cat, [])
            if not data_source:
                continue
            choices = {i: item["title"] for i, item in enumerate(data_source)}

            matches = process.extract(
                query,
                choices,
                limit=15,
                scorer=fuzz.partial_ratio
            )

            cat_results = []
            for title, score, index in matches:
                if score > 80:
                    obj = data_source[index]
                    cat_results.append({
                        "id": obj["id"],
                        "title": obj["title"],
                        "type": cat,
                        "score": score
                    })

            results.extend(cat_results)

        def get_sort_key(item, sort_query):
            normalized_query = sort_query.lower().strip()
            title_lower = item["title"].lower()
            starts_with = 0 if title_lower.startswith(normalized_query) else 1
            score_part = -(int(item["score"]) // 5)
            last_name = item["title"].split()[0]
            return starts_with, score_part, last_name

        results.sort(key=lambda x: get_sort_key(x, query))

        return SearchResponse(results=[
            SearchItem(
                id=result["id"],
                title=result["title"],
                type=result["type"]
            ) for result in results
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
