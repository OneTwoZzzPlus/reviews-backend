import csv
import hashlib
from collections.abc import AsyncGenerator
from io import StringIO

import httpx
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_database
from enums import SuggestionStatus
from models.content import Processed, Suggestion


class GSParserService:
    class MainException(Exception):
        pass

    class InvalidGSheet(MainException):
        pass

    class InaccessibleGSheet(MainException):
        pass

    SHEET_ID = "1TFTOKxqml1agwgo6Vp0Ql6Rgj9f9ciyOqQPF8VvUkJQ"
    SHEET_NAME = "Ответы на форму (1)"
    COLUMN_DATE = 0
    COLUMN_TEACHER = 1
    COLUMN_SUBJECT = 2
    COLUMN_REVIEW = 3

    def __init__(self, session: AsyncSession):
        self.session = session
        self.url = f"https://docs.google.com/spreadsheets/d/{self.SHEET_ID}/gviz/tq?tqx=out:csv&sheet={self.SHEET_NAME}"
        self.columns_ids = [
            self.COLUMN_DATE,
            self.COLUMN_TEACHER,
            self.COLUMN_SUBJECT,
            self.COLUMN_REVIEW,
        ]

    async def load_sheet(self) -> list[list[str]]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url, follow_redirects=True)
                response.raise_for_status()

            reader = csv.reader(StringIO(response.text))
            rows = list(reader)
            if not rows:
                raise GSParserService.InvalidGSheet("Invalid sheet: no data found.")
            return rows
        except httpx.HTTPStatusError as err:
            raise GSParserService.InaccessibleGSheet(
                f"Inaccessible sheet: ({err.response.status_code}) {err.response.text}"
            )
        except httpx.RequestError as err:
            raise GSParserService.InaccessibleGSheet(f"Request failed: {err}")

    def generate_row_id(self, row: list[str]) -> str:
        """Creates a unique MD5 hash"""
        unique_string = ""
        for column_index in self.columns_ids:
            unique_string += (
                row[column_index].strip() if len(row) > column_index else ""
            )
        return hashlib.md5(unique_string.encode("utf-8")).hexdigest()

    @staticmethod
    def convert_datetime(s: str) -> str:
        """Converts a datetime string"""
        try:
            date_part, time_part = s.split()
            day, month, year = date_part.split(".")
            hour, minute, _ = time_part.split(":")
            return f"{hour}:{minute} {day}.{month}.{year}"
        except ValueError:
            return "00:00 00.00.2023"

    async def parse(self) -> int:
        counter = 0
        rows = await self.load_sheet()

        stmt = select(Processed.id)
        res = await self.session.scalars(stmt)
        processed_ids = set(res.all())

        for row in rows:
            if not any(row):
                continue

            row_id = self.generate_row_id(row)
            if row_id in processed_ids:
                continue

            date = row[self.COLUMN_DATE] if len(row) > self.COLUMN_DATE else ""
            date = self.convert_datetime(date)
            teacher = row[self.COLUMN_TEACHER] if len(row) > self.COLUMN_TEACHER else ""
            subject = row[self.COLUMN_SUBJECT] if len(row) > self.COLUMN_SUBJECT else ""
            review = row[self.COLUMN_REVIEW] if len(row) > self.COLUMN_REVIEW else ""

            suggestion = Suggestion(
                status=SuggestionStatus.delayed,
                source_id=2,
                date=date,
                teacher_title=teacher,
                subject_title=subject,
                text=review,
            )
            processed = Processed(id=row_id)

            self.session.add(suggestion)
            self.session.add(processed)

            processed_ids.add(row_id)
            counter += 1

        if counter > 0:
            await self.session.commit()

        return counter


async def get_gsparser_service(
    session: AsyncSession = Depends(get_database),
) -> AsyncGenerator[GSParserService, None]:
    yield GSParserService(session=session)
