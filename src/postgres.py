import asyncpg

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

    async def select_search(self, query: str) -> SearchResponse:
        async with self.pool.acquire() as conn:
            teachers = await conn.fetch("SELECT id, name FROM public.teacher WHERE name ILIKE $1", f"%{query}%")
            subjects = await conn.fetch("SELECT id, title FROM public.subject WHERE title ILIKE $1", f"%{query}%")
            results = []
            for s in subjects:
                results.append(SearchItem(id=s["id"], title=s["title"], type=SearchType.subject))
            for t in teachers:
                results.append(SearchItem(id=t["id"], title=t["name"], type=SearchType.teacher))
            if results:
                return SearchResponse(results=results)
        return None

    async def select_teacher(self, iid: int) -> TeacherResponse:
        async with self.pool.acquire() as conn:
            head = await conn.fetchrow("SELECT id, name FROM public.teacher WHERE id = $1", iid)
            if not head:
                return None
            summaries = await conn.fetch("SELECT id, title, value FROM public.summary WHERE teacher_id = $1", iid)
            comments = await conn.fetch("""
                SELECT 
                    c.id   AS id,
                    c.date AS date, 
                    c.text AS text, 
                    source.id     AS source_id, 
                    source.title  AS source_title, 
                    source.link   AS source_link,
                    subject.id    AS subject_id,
                    subject.title AS subject_title
                FROM public.comment AS c
                JOIN public.source AS source ON c.source_id = source.id
                JOIN public.subject AS subject ON c.subject_id = subject.id
                WHERE teacher_id = $1
            """, iid)

            return TeacherResponse(
                id=head["id"], name=head["name"], rating=0,
                summaries=[Summary(title=s["title"], value=s["value"]) for s in summaries],
                comments=[Comment(
                    id=c["id"], date=c["date"], text=c["text"], karma=0,
                    source=Source(title=c["source_title"], link=c["source_link"]),
                    subject=Subject(title=c["subject_title"])
                ) for c in comments]
            )

    async def select_subject(self, iid: int) -> SubjectResponse:
        async with self.pool.acquire() as conn:
            subject = await conn.fetchrow(
                "SELECT id, title FROM public.subject WHERE id = $1",
                iid
            )

            if not subject:
                return None

            teachers_raw = await conn.fetch(
                """
                SELECT t.id, t.name
                FROM public.teacher t
                JOIN public.relationst r ON r.teacher_id = t.id
                WHERE r.subject_id = $1
                """,
                iid
            )

            teacher_ids = [t["id"] for t in teachers_raw]
            if not teacher_ids:
                return SubjectResponse(
                    id=subject["id"],
                    title=subject["title"],
                    teachers=[]
                )

            summaries = await conn.fetch(
                """
                SELECT id, title, value, teacher_id
                FROM public.summary
                WHERE teacher_id = ANY($1)
                """,
                teacher_ids
            )

            comments = await conn.fetch(
                """
                SELECT
                    c.id,
                    c.date,
                    c.text,
                    c.teacher_id,
                    
                    source.id    AS source_id,
                    source.title AS source_title,
                    source.link  AS source_link,
                    
                    subject.id    AS subject_id,
                    subject.title AS subject_title
                FROM public.comment c
                JOIN public.source  source  ON c.source_id = source.id
                JOIN public.subject subject ON c.subject_id = subject.id
                WHERE c.teacher_id = ANY($1)
                """,
                teacher_ids
            )

        teachers = {
            t["id"]: TeacherResponse(
                id=t["id"], name=t["name"], rating=0,
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
                    id=c["id"], date=c["date"], text=c["text"], karma=0,
                    source=Source(title=c["source_title"], link=c["source_link"]),
                    subject=Subject(title=c["subject_title"]),
                )
            )

        return SubjectResponse(
            id=subject["id"],
            title=subject["title"],
            teachers=list(teachers.values()),
        )
