import re
from datetime import datetime, timezone, timedelta
from rapidfuzz import fuzz
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from core.database import AsyncSession, get_database
from enums import SearchType, SuggestionStatus
from models.reviews import Subject, Teacher, Comment, RelationST
from models.content import (
    Suggestion,
    TeacherRating,
    CommentKarma,
    Moderator,
    Processed,
)
from schemas.reviews import (
    SearchResponse,
    SearchItem,
    TeacherResponse,
    SummarySchema,
    CommentSchema,
    SourceSchema,
    SubjectSchema,
    SubjectResponse,
    TeacherRateResponse,
    CommentKarmaResponse,
    SuggestionAddRequest,
    SuggestionAddResponse,
    SuggestionListResponse,
    SuggestionItem,
    SuggestionResponse,
    InputItem,
    SuggestionCommitRequest,
    SuggestionCommitResponse,
    SuggestionCancelRequest,
    SuggestionCancelResponse,
    TeacherUpdateRequest,
    TeacherUpdateResponse,
    SubjectUpdateRequest,
    SubjectUpdateResponse,
    CommentAddRequest,
    CommentAddResponse,
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
    current_time = datetime.now(timezone.utc).astimezone(utc_plus_3)
    return current_time.strftime("%H:%M %d.%m.%Y")


class ReviewsService:
    # static cache variables
    _teachers_cache: list[dict] = []
    _subjects_cache: list[dict] = []
    _cache_loaded: bool = False

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

    async def teacher(self, iid: int, isu: int | None = None) -> TeacherResponse | None:
        stmt = (
            select(Teacher)
            .options(
                selectinload(Teacher.summaries),
                selectinload(Teacher.ratings),
                selectinload(Teacher.comments).joinedload(Comment.source),
                selectinload(Teacher.comments).joinedload(Comment.subject),
                selectinload(Teacher.comments).selectinload(Comment.karmas),
            )
            .where(Teacher.id == iid)
        )

        if isu:
            stmt = stmt.options(
                with_loader_criteria(TeacherRating, TeacherRating.isu == isu),
                with_loader_criteria(CommentKarma, CommentKarma.isu == isu),
            )

        teacher_obj = await self.session.scalar(stmt)
        if not teacher_obj:
            return None

        return TeacherResponse(
            id=teacher_obj.id,
            name=teacher_obj.name,
            rating=teacher_obj.rating,
            user_rating=teacher_obj.user_rating if isu else None,
            summaries=[
                SummarySchema(title=s.title, value=s.value)
                for s in teacher_obj.summaries
            ],
            comments=[
                CommentSchema(
                    id=c.id,
                    date=c.date,
                    text=c.text,
                    karma=c.karma,
                    user_karma=c.user_karma if isu else None,
                    source=SourceSchema(title=c.source.title, link=c.source.link)
                    if c.source
                    else None,
                    subject=SubjectSchema(title=c.subject.title) if c.subject else None,
                )
                for c in teacher_obj.comments
            ],
        )

    async def subject(self, iid: int, isu: int | None = None) -> SubjectResponse | None:
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.teachers).selectinload(Teacher.summaries),
                selectinload(Subject.teachers).selectinload(Teacher.ratings),
                selectinload(Subject.teachers)
                .selectinload(Teacher.comments)
                .joinedload(Comment.source),
                selectinload(Subject.teachers)
                .selectinload(Teacher.comments)
                .joinedload(Comment.subject),
                selectinload(Subject.teachers)
                .selectinload(Teacher.comments)
                .selectinload(Comment.karmas),
            )
            .where(Subject.id == iid)
        )

        if isu:
            stmt = stmt.options(
                with_loader_criteria(TeacherRating, TeacherRating.isu == isu),
                with_loader_criteria(CommentKarma, CommentKarma.isu == isu),
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
                    rating=t.rating,
                    user_rating=t.user_rating if isu else None,
                    summaries=[
                        SummarySchema(title=s.title, value=s.value) for s in t.summaries
                    ],
                    comments=[
                        CommentSchema(
                            id=c.id,
                            date=c.date,
                            text=c.text,
                            karma=c.karma,
                            user_karma=c.user_karma if isu else None,
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

    async def teacher_rate(
        self, isu: int, iid: int, rating: int
    ) -> TeacherRateResponse | None:
        try:
            stmt = pg_insert(TeacherRating).values(
                isu=isu, teacher_id=iid, user_rating=rating
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["isu", "teacher_id"],
                set_={"user_rating": stmt.excluded.user_rating},
            )
            await self.session.execute(stmt)
            await self.session.commit()

            teacher_obj = await self.teacher(iid, isu=isu)
            if not teacher_obj:
                return None

            return TeacherRateResponse(
                rating=teacher_obj.rating,
                user_rating=teacher_obj.user_rating or 0,
            )
        except IntegrityError as e:
            await self.session.rollback()
            print(e)
            return None

    async def comment_vote(
        self, isu: int, iid: int, karma: int
    ) -> CommentKarmaResponse | None:
        try:
            stmt = pg_insert(CommentKarma).values(
                isu=isu, comment_id=iid, user_karma=karma
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["isu", "comment_id"],
                set_={"user_karma": stmt.excluded.user_karma},
            )
            await self.session.execute(stmt)
            await self.session.commit()

            comment_stmt = (
                select(Comment)
                .options(
                    selectinload(Comment.karmas),
                    with_loader_criteria(CommentKarma, CommentKarma.isu == isu),
                )
                .where(Comment.id == iid)
            )
            comment_obj = await self.session.scalar(comment_stmt)
            if not comment_obj:
                return None

            return CommentKarmaResponse(
                karma=comment_obj.karma,
                user_karma=comment_obj.user_karma or 0,
            )
        except IntegrityError as e:
            await self.session.rollback()
            print(e)
            return None

    async def add_suggestion(
        self, isu: int | None, data: SuggestionAddRequest
    ) -> SuggestionAddResponse:
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
            user_isu=isu,
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

    async def list_suggestion(
        self, delayed=True, accepted=False, rejected=False
    ) -> SuggestionListResponse:
        statuses = []
        if delayed:
            statuses.append(SuggestionStatus.delayed)
        if accepted:
            statuses.append(SuggestionStatus.accepted)
        if rejected:
            statuses.append(SuggestionStatus.rejected)

        stmt = select(Suggestion).where(Suggestion.status.in_(statuses))
        suggestions = (await self.session.scalars(stmt)).all()

        return SuggestionListResponse(
            items=[
                SuggestionItem(
                    id=s.id,
                    status=s.status,
                    title=s.teacher_title,
                    source_id=s.source_id,
                )
                for s in suggestions
            ]
        )

    async def get_suggestion(self, iid: int) -> SuggestionResponse | None:
        s = await self.session.get(Suggestion, iid)
        if s is None:
            return None

        subs = []
        if s.subs_id and s.subs_title:
            for x_id, x_title in zip(s.subs_id.split(";"), s.subs_title.split(";")):
                subs.append(
                    InputItem(id=None if x_id == "" else int(x_id), title=x_title)
                )

        return SuggestionResponse(
            id=s.id,
            status=s.status,
            user_isu=s.user_isu,
            moderator_isu=s.moderator_isu,
            text=s.text,
            teacher=InputItem(id=s.teacher_id, title=s.teacher_title),
            subject=InputItem(id=s.subject_id, title=s.subject_title),
            subs=subs,
            comment_id=s.comment_id,
        )

    async def commit_suggestion(
        self, isu: int, iid: int, body: SuggestionCommitRequest
    ) -> SuggestionCommitResponse | None:
        try:
            suggestion = await self.session.get(Suggestion, iid)
            if not suggestion:
                return None

            comment = Comment(
                date=suggestion.date,
                source_id=suggestion.source_id,
                text=body.text,
                subject_id=body.subject.id,
                teacher_id=body.teacher.id,
            )
            self.session.add(comment)
            await self.session.flush()

            for s in body.subs + [body.subject]:
                rel_stmt = (
                    pg_insert(RelationST)
                    .values(subject_id=s.id, teacher_id=body.teacher.id)
                    .on_conflict_do_nothing()
                )
                await self.session.execute(rel_stmt)

            suggestion.status = SuggestionStatus.accepted
            suggestion.moderator_isu = isu
            suggestion.comment_id = comment.id

            await self.session.commit()
            return SuggestionCommitResponse(comment_id=comment.id)
        except IntegrityError as e:
            await self.session.rollback()
            print(e)
            return None

    async def cancel_suggestion(
        self, isu: int, iid: int, body: SuggestionCancelRequest
    ) -> SuggestionCancelResponse | None:
        try:
            suggestion = await self.session.get(Suggestion, iid)
            if not suggestion:
                return None

            suggestion.status = body.status
            suggestion.moderator_isu = isu
            await self.session.commit()
            return SuggestionCancelResponse(status=body.status)
        except IntegrityError as e:
            await self.session.rollback()
            print(e)
            return None

    async def upsert_teacher(self, data: TeacherUpdateRequest) -> TeacherUpdateResponse:
        stmt = pg_insert(Teacher).values(id=data.id, name=data.title)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"name": stmt.excluded.name},
        )
        await self.session.execute(stmt)
        await self.session.commit()
        await self.reload_cache()
        return TeacherUpdateResponse(id=data.id)

    async def upsert_subject(self, data: SubjectUpdateRequest) -> SubjectUpdateResponse:
        if data.id is None:
            subject = Subject(title=data.title)
            self.session.add(subject)
            await self.session.commit()
            subject_id = subject.id
        else:
            stmt = pg_insert(Subject).values(id=data.id, title=data.title)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={"title": stmt.excluded.title},
            )
            await self.session.execute(stmt)
            await self.session.commit()
            subject_id = data.id

        await self.reload_cache()
        return SubjectUpdateResponse(id=subject_id)

    async def add_comment(self, data: CommentAddRequest) -> CommentAddResponse:
        comment = Comment(
            date=data.date,
            text=data.text,
            source_id=data.source_id,
            subject_id=data.subject.id,
            teacher_id=data.teacher.id,
        )
        self.session.add(comment)
        await self.session.flush()

        for s in data.subs + [data.subject]:
            rel_stmt = (
                pg_insert(RelationST)
                .values(subject_id=s.id, teacher_id=data.teacher.id)
                .on_conflict_do_nothing()
            )
            await self.session.execute(rel_stmt)

        await self.session.commit()
        return CommentAddResponse(id=comment.id)

    async def select_moderators(self) -> dict[int, None]:
        stmt = select(Moderator.isu).where(Moderator.access)
        res = await self.session.scalars(stmt)
        return {int(isu): None for isu in res.all()}

    async def select_gs_processed(self) -> set[str]:
        stmt = select(Processed.id)
        res = await self.session.scalars(stmt)
        return set(res.all())

    async def insert_gs_suggestion(
        self, row_id: str, date: str, teacher: str, subject: str, review: str
    ) -> int:
        suggestion = Suggestion(
            status=SuggestionStatus.delayed,
            source_id=2,
            date=date,
            teacher_title=teacher,
            subject_title=subject,
            text=review,
        )
        self.session.add(suggestion)

        processed = Processed(id=row_id)
        self.session.add(processed)

        await self.session.commit()
        return suggestion.id


async def get_reviews_service(
    session: AsyncSession = Depends(get_database),
) -> AsyncGenerator[ReviewsService, None]:
    yield ReviewsService(session=session)
