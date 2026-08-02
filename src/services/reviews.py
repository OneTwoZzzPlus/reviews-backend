import re
import string
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta, timezone
from typing import ClassVar

from fastapi import Depends
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.cache import get_data_version
from core.database import AsyncSession, get_database
from enums.reviews import SearchType, SuggestionStatus
from models.content import Suggestion
from models.insights import Insights as InsightsModel
from models.reviews import Comment, Subject, Teacher
from schemas.insights import (
    Confidence,
    Difficulty,
    GradingFairness,
    Insights,
    InsightsEssential,
    InsightsShort,
    Organization,
    Rating,
    Scores,
    Strictness,
    StudentAttitude,
    Teaching,
    Workload,
)
from schemas.reviews import (
    CommentSchema,
    RegistryResponse,
    SearchItem,
    SearchResponse,
    SourceSchema,
    SubjectResponse,
    SubjectSchema,
    SuggestionRequest,
    SuggestionResponse,
    SummarySchema,
    TeacherResponse,
    TeacherShort,
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


def review_section(text: str) -> str:
    words = text.split()
    if len(words) < 30:
        return text
    selected = words[:20]
    selected[-1] = selected[-1].rstrip(string.punctuation)
    return " ".join(selected) + "..."


def get_current_time():
    utc_plus_3 = timezone(timedelta(hours=3))
    current_time = datetime.now(UTC).astimezone(utc_plus_3)
    return current_time.strftime("%H:%M %d.%m.%Y")


class ReviewsService:
    # static cache variables
    _version = None
    _teachers_cache: ClassVar[list[dict]] = []
    _subjects_cache: ClassVar[list[dict]] = []
    _registry: ClassVar[RegistryResponse] = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def reload_cache(self):
        """Loading the search and registry cache"""

        current = get_data_version()
        if ReviewsService._version == current:
            return

        # /search

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

        # /registry

        stmt = select(InsightsModel).options(selectinload(InsightsModel.teacher))
        results = await self.session.execute(stmt)
        original = {}
        normalized = {}
        insights = {}
        for ins in results.scalars():
            if ins.teacher is None:
                continue
            id, name = ins.teacher.id, ins.teacher.name
            original[name] = id
            normalized["".join(name.split()).lower()] = id
            insights[id] = InsightsEssential(
                rating_value=ins.rating_value, confidence_value=ins.confidence_value
            )
        ReviewsService._registry = RegistryResponse(
            original=original,
            normalized=normalized,
            insights=insights,
        )

        ReviewsService._version = current

    async def registry(self) -> RegistryResponse:
        await self.reload_cache()
        return ReviewsService._registry

    async def search(self, query: str, strainer: str | None) -> SearchResponse:
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
                selectinload(Teacher.insight),
                selectinload(Teacher.summaries),
                selectinload(Teacher.comments).joinedload(Comment.source),
                selectinload(Teacher.comments).joinedload(Comment.subject),
            )
            .where(Teacher.id == iid)
        )

        t = await self.session.scalar(stmt)
        if not t:
            return None

        insights = None
        if t.insight:
            i = t.insight
            insights = Insights(
                summary=i.summary,
                pros=i.pros,
                cons=i.cons,
                highlights=i.highlights,
                rating=Rating(value=i.rating_value, reason=i.rating_reason),
                confidence=Confidence(
                    value=i.confidence_value, reason=i.confidence_reason
                ),
                scores=Scores(
                    teaching=Teaching(value=i.teaching_value, reason=i.teaching_reason),
                    student_attitude=StudentAttitude(
                        value=i.student_attitude_value, reason=i.student_attitude_reason
                    ),
                    organization=Organization(
                        value=i.organization_value, reason=i.organization_reason
                    ),
                    grading_fairness=GradingFairness(
                        value=i.grading_fairness_value, reason=i.grading_fairness_reason
                    ),
                    strictness=Strictness(
                        value=i.strictness_value, reason=i.strictness_reason
                    ),
                    workload=Workload(value=i.workload_value, reason=i.workload_reason),
                    difficulty=Difficulty(
                        value=i.difficulty_value, reason=i.difficulty_reason
                    ),
                ),
            )

        return TeacherResponse(
            id=t.id,
            name=t.name,
            insights=insights,
            summaries=[
                SummarySchema(title=summ.title, value=summ.value)
                for summ in t.summaries
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
                for c in t.comments
            ],
        )

    async def subject(self, iid: int) -> SubjectResponse | None:
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.teachers).selectinload(Teacher.insight),
                selectinload(Subject.teachers).selectinload(Teacher.comments),
            )
            .where(Subject.id == iid)
        )

        s = await self.session.scalar(stmt)
        if not s:
            return None

        return SubjectResponse(
            id=s.id,
            title=s.title,
            teachers=[
                TeacherShort(
                    id=t.id,
                    name=t.name,
                    alt=review_section(t.comments[-1].text) if t.comments else None,
                    insights=InsightsShort(
                        summary=t.insight.summary,
                        pros=t.insight.pros,
                        cons=t.insight.cons,
                        highlights=t.insight.highlights,
                        rating=Rating(
                            value=t.insight.rating_value, reason=t.insight.rating_reason
                        ),
                        confidence=Confidence(
                            value=t.insight.confidence_value,
                            reason=t.insight.confidence_reason,
                        ),
                    )
                    if t.insight
                    else None,
                )
                for t in s.teachers
            ],
        )

    async def add_suggestion(self, data: SuggestionRequest) -> SuggestionResponse:
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
        return SuggestionResponse(id=suggestion.id)


async def get_reviews_service(
    session: AsyncSession = Depends(get_database),
) -> AsyncGenerator[ReviewsService, None]:
    yield ReviewsService(session=session)
