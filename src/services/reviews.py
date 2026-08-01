import re
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta, timezone
from typing import ClassVar

from fastapi import Depends
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import AsyncSession, get_database
from enums import SearchType, SuggestionStatus
from models.content import Suggestion
from models.reviews import Comment, Subject, Teacher
from schemas.reviews import (
    CommentSchema,
    SearchItem,
    SearchResponse,
    SourceSchema,
    SubjectResponse,
    SubjectSchema,
    SuggestionAddRequest,
    SuggestionAddResponse,
    SummarySchema,
    TeacherResponse,
)


def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    text = re.sub(r"(.)\1+", r"\1", text)
    text = re.sub(r"[^а-яa-z0-9\s]", "", text)
    text = " ".join(text.split())
    return text


def get_current_time():
    utc_plus_3 = timezone(timedelta(hours=3))
    current_time = datetime.now(UTC).astimezone(utc_plus_3)
    return current_time.strftime("%H:%M %d.%m.%Y")


class ReviewsService:
    # static cache variables
    _teachers_cache: ClassVar[list[dict]] = []
    _subjects_cache: ClassVar[list[dict]] = []
    _cache_loaded: ClassVar[bool] = False

    def __init__(self, session: AsyncSession):
        self.session = session

    async def reload_cache(self):
        """Loading the search cache"""
        teachers_stmt = select(Teacher.id, Teacher.name)
        teachers_res = await self.session.execute(teachers_stmt)
        ReviewsService._teachers_cache = [
            {"title": name, "id": t_id} for t_id, name in teachers_res.all()
        ]

        subjects_stmt = select(Subject.id, Subject.title)
        subjects_res = await self.session.execute(subjects_stmt)
        ReviewsService._subjects_cache = [
            {"title": title, "id": s_id} for s_id, title in subjects_res.all()
        ]

        ReviewsService._cache_loaded = True

    async def search(self, query: str, strainer: str | None) -> SearchResponse:
        if not ReviewsService._cache_loaded:
            await self.reload_cache()

        normalized_query = normalize(query)
        if not normalized_query:
            return SearchResponse(results=[])

        cache = {
            SearchType.teacher: ReviewsService._teachers_cache,
            SearchType.subject: ReviewsService._subjects_cache,
        }

        categories = (
            [strainer] if strainer else [SearchType.teacher, SearchType.subject]
        )
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
                    raw_results.append(
                        {
                            "id": item["id"],
                            "title": original_title,
                            "type": cat,
                            "score": score,
                            "priority": priority,
                        }
                    )

        raw_results.sort(
            key=lambda x: (x["priority"], -x["score"], x["title"].split()[0])
        )

        return SearchResponse(
            results=[
                SearchItem(id=res["id"], title=res["title"], type=res["type"])
                for res in raw_results[:20]
            ]
        )

    async def teacher(self, iid: int) -> TeacherResponse | None:
        stmt = (
            select(Teacher)
            .options(
                selectinload(Teacher.summaries),
                selectinload(Teacher.comments).joinedload(Comment.source),
                selectinload(Teacher.comments).joinedload(Comment.subject),
            )
            .where(Teacher.id == iid)
        )

        teacher_obj = await self.session.scalar(stmt)
        if not teacher_obj:
            return None

        return TeacherResponse(
            id=teacher_obj.id,
            name=teacher_obj.name,
            summaries=[
                SummarySchema(title=s.title, value=s.value)
                for s in teacher_obj.summaries
            ],
            comments=[
                CommentSchema(
                    id=c.id,
                    date=c.date,
                    text=c.text,
                    source=SourceSchema(title=c.source.title, link=c.source.link)
                    if c.source
                    else None,
                    subject=SubjectSchema(title=c.subject.title) if c.subject else None,
                )
                for c in teacher_obj.comments
            ],
        )

    async def subject(self, iid: int) -> SubjectResponse | None:
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.teachers).selectinload(Teacher.summaries),
                selectinload(Subject.teachers)
                .selectinload(Teacher.comments)
                .joinedload(Comment.source),
                selectinload(Subject.teachers)
                .selectinload(Teacher.comments)
                .joinedload(Comment.subject),
                selectinload(Subject.teachers).selectinload(Teacher.comments),
            )
            .where(Subject.id == iid)
        )

        subject_obj = await self.session.scalar(stmt)
        if not subject_obj:
            return None

        return SubjectResponse(
            id=subject_obj.id,
            title=subject_obj.title,
            teachers=[
                TeacherResponse(
                    id=t.id,
                    name=t.name,
                    summaries=[
                        SummarySchema(title=s.title, value=s.value) for s in t.summaries
                    ],
                    comments=[
                        CommentSchema(
                            id=c.id,
                            date=c.date,
                            text=c.text,
                            source=SourceSchema(
                                title=c.source.title, link=c.source.link
                            )
                            if c.source
                            else None,
                            subject=SubjectSchema(title=c.subject.title)
                            if c.subject
                            else None,
                        )
                        for c in t.comments
                    ],
                )
                for t in subject_obj.teachers
            ],
        )

    async def add_suggestion(self, data: SuggestionAddRequest) -> SuggestionAddResponse:
        subs_id = (
            ";".join(["" if x.id is None else str(x.id) for x in data.subs])
            if data.subs
            else None
        )
        subs_title = (
            ";".join(
                ["" if x.title is None else x.title.replace(";", "") for x in data.subs]
            )
            if data.subs
            else None
        )

        suggestion = Suggestion(
            status=SuggestionStatus.delayed,
            text=data.text,
            teacher_id=data.teacher.id,
            teacher_title=data.teacher.title,
            subject_id=data.subject.id,
            subject_title=data.subject.title,
            subs_id=subs_id,
            subs_title=subs_title,
            date=get_current_time(),
        )
        self.session.add(suggestion)
        await self.session.commit()
        return SuggestionAddResponse(id=suggestion.id)


async def get_reviews_service(
    session: AsyncSession = Depends(get_database),
) -> AsyncGenerator[ReviewsService, None]:
    yield ReviewsService(session=session)
