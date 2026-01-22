from os import access

import asyncpg
from asyncpg.exceptions import ForeignKeyViolationError

from src.models import *


class Postgres:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.conn_str,
            min_size=1,
            max_size=10
        )

    async def disconnect(self):
        await self.pool.close()

    async def select_search(self, query: str, strainer: str | None) -> SearchResponse:
        async with self.pool.acquire() as conn:
            results = []

            if strainer is None or strainer == SearchType.teacher:
                teachers = await conn.fetch("SELECT id, name FROM public.teacher WHERE name ILIKE $1;", f"%{query}%")
                for t in teachers:
                    results.append(SearchItem(id=t["id"], title=t["name"], type=SearchType.teacher))

            if strainer is None or strainer == SearchType.subject:
                subjects = await conn.fetch("SELECT id, title FROM public.subject WHERE title ILIKE $1;", f"%{query}%")
                for s in subjects:
                    results.append(SearchItem(id=s["id"], title=s["title"], type=SearchType.subject))

            if results:
                return SearchResponse(results=results)

        return None

    async def select_teacher(self, t_id: int, isu: int = 0) -> TeacherResponse:
        async with self.pool.acquire() as conn:
            head = await conn.fetchrow("""
                SELECT 
                    t.id   AS id, 
                    t.name AS name,
                    public.get_avg_teacher_rating(t.id) AS rating,
                    COALESCE(tr.user_rating, 0) AS user_rating
                FROM public.teacher AS t
                LEFT JOIN public.teacher_rating AS tr 
                    ON t.id = tr.teacher_id AND tr.isu = $2
                WHERE t.id = $1;
                """, t_id, isu)
            if not head:
                return None
            summaries = await conn.fetch("SELECT id, title, value FROM public.summary WHERE teacher_id = $1;", t_id)
            comments = await conn.fetch("""
                SELECT 
                    c.id   AS id,
                    c.date AS date, 
                    c.text AS text, 
                    source.id     AS source_id, 
                    source.title  AS source_title, 
                    source.link   AS source_link,
                    subject.id    AS subject_id,
                    subject.title AS subject_title,
                    
                    public.get_comment_karma(c.id) AS karma,
                    COALESCE(ck.user_karma, 0) AS user_karma
                
                FROM public.comment AS c
                JOIN public.source AS source ON c.source_id = source.id
                JOIN public.subject AS subject ON c.subject_id = subject.id
                LEFT JOIN public.comment_karma AS ck 
                    ON c.id = ck.comment_id AND ck.isu = $2
                
                WHERE c.teacher_id = $1;
                """, t_id, isu)

            return TeacherResponse(
                id=head["id"], name=head["name"],
                rating=head["rating"],
                user_rating=head["user_rating"] if isu != 0 else None,
                summaries=[Summary(title=s["title"], value=s["value"]) for s in summaries],
                comments=[Comment(
                    id=c["id"], date=c["date"], text=c["text"],
                    karma=c["karma"],
                    user_karma=c["user_karma"] if isu != 0 else None,
                    source=Source(title=c["source_title"], link=c["source_link"]),
                    subject=Subject(title=c["subject_title"])
                ) for c in comments]
            )

    async def select_subject(self, s_id: int, isu: int = 0) -> SubjectResponse:
        async with self.pool.acquire() as conn:
            subject = await conn.fetchrow("SELECT id, title FROM public.subject WHERE id = $1;", s_id)

            if not subject:
                return None

            teachers_raw = await conn.fetch("""
                SELECT 
                    t.id   AS id, 
                    t.name AS name,
                    public.get_avg_teacher_rating(t.id) AS rating,
                    COALESCE(tr.user_rating, 0) AS user_rating
                FROM public.teacher t
                JOIN public.relationst r ON r.teacher_id = t.id
                LEFT JOIN public.teacher_rating AS tr 
                    ON t.id = tr.teacher_id AND tr.isu = $2
                WHERE r.subject_id = $1;
                """, s_id, isu)

            teacher_ids = [t["id"] for t in teachers_raw]
            if not teacher_ids:
                return SubjectResponse(
                    id=subject["id"],
                    title=subject["title"],
                    teachers=[]
                )

            summaries = await conn.fetch("""
                SELECT id, title, value, teacher_id
                FROM public.summary
                WHERE teacher_id = ANY($1);
                """, teacher_ids)

            comments = await conn.fetch("""
                SELECT
                    c.id   AS id,
                    c.date AS date,
                    c.text AS text,
                    c.teacher_id AS teacher_id,
                    
                    source.id    AS source_id,
                    source.title AS source_title,
                    source.link  AS source_link,
                    subject.id    AS subject_id,
                    subject.title AS subject_title,
                    
                    public.get_comment_karma(c.id) AS karma,
                    COALESCE(ck.user_karma, 0) AS user_karma
                    
                FROM public.comment c
                JOIN public.source  source  ON c.source_id = source.id
                JOIN public.subject subject ON c.subject_id = subject.id
                LEFT JOIN public.comment_karma AS ck 
                    ON c.id = ck.comment_id AND ck.isu = $2
                WHERE c.teacher_id = ANY($1);
                """, teacher_ids, isu)

        teachers = {
            t["id"]: TeacherResponse(
                id=t["id"], name=t["name"],
                rating=t["rating"],
                user_rating=t["user_rating"] if isu != 0 else None,
                summaries=[], comments=[],
            ) for t in teachers_raw
        }

        for s in summaries:
            teachers[s["teacher_id"]].summaries.append(
                Summary(title=s["title"], value=s["value"])
            )

        for c in comments:
            teachers[c["teacher_id"]].comments.append(
                Comment(
                    id=c["id"], date=c["date"], text=c["text"],
                    karma=c["karma"],
                    user_karma=c["user_karma"] if isu != 0 else None,
                    source=Source(title=c["source_title"], link=c["source_link"]),
                    subject=Subject(title=c["subject_title"]),
                )
            )

        return SubjectResponse(
            id=subject["id"],
            title=subject["title"],
            teachers=list(teachers.values()),
        )

    async def upsert_teacher_rating(self, isu: int, t_id: int, user_rating: int) -> bool:
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO public.teacher_rating (isu, teacher_id, user_rating)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (isu, teacher_id) 
                    DO UPDATE SET user_rating = EXCLUDED.user_rating;
                    """, isu, t_id, user_rating)

                row = await conn.fetchrow("""        
                    SELECT
                        public.get_avg_teacher_rating(t.id) AS rating,
                        COALESCE(tr.user_rating, 0) AS user_rating
                    FROM public.teacher AS t
                    LEFT JOIN public.teacher_rating AS tr 
                        ON t.id = tr.teacher_id AND tr.isu = $1
                    WHERE t.id = $2;
                    """, isu, t_id)

                return TeacherRateResponse(
                    rating=row["rating"],
                    user_rating=row["user_rating"]
                )
            except ForeignKeyViolationError as e:
                print(e)
                return None

    async def upsert_comment_karma(self, isu: int, c_id: int, user_karma: int) -> bool:
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO public.comment_karma (isu, comment_id, user_karma)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (isu, comment_id) 
                    DO UPDATE SET user_karma = EXCLUDED.user_karma;
                    """, isu, c_id, user_karma)

                row = await conn.fetchrow("""
                    SELECT
                        public.get_comment_karma(c.id) AS karma,
                        COALESCE(ck.user_karma, 0) AS user_karma
                    FROM public.comment AS c
                    LEFT JOIN public.comment_karma AS ck 
                        ON c.id = ck.comment_id AND ck.isu = $1
                    WHERE c.id = $2;
                    """, isu, c_id)

                return CommentKarmaResponse(
                    karma=row["karma"],
                    user_karma=row["user_karma"]
                )
            except ForeignKeyViolationError:
                print(e)
                return None

    async def insert_suggestion(self, user_isu: int | None, data: SuggestionAddRequest) -> bool:
        async with self.pool.acquire() as conn:
            suggestion_id = await conn.fetchval(
                """
                INSERT INTO public.suggestion(
                    status, user_isu, text, teacher_id, teacher_title, 
                    subject_id, subject_title, subs_id, subs_title)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id;
                """,
                SuggestionStatus.check,
                user_isu,
                data.comment,
                data.teacher.id,
                data.teacher.title,
                data.subject.id,
                data.subject.title,
                ';'.join(['' if x is None else str(x.id) for x in data.subs]),
                ';'.join(['' if x is None else x.title.replace(';', '') for x in data.subs])
            )
            return suggestion_id

    async def select_moderators(self):
        async with self.pool.acquire() as conn:
            mods = await conn.fetch("SELECT * FROM public.moderator WHERE access = TRUE;")
            return {int(m['isu']): None for m in mods}
