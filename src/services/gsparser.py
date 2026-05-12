import hashlib
import requests
import csv
from io import StringIO


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

    def __init__(self, database):
        self.database = database
        self.url = f"https://docs.google.com/spreadsheets/d/{self.SHEET_ID}/gviz/tq?tqx=out:csv&sheet={self.SHEET_NAME}"
        self.columns_ids = [self.COLUMN_DATE, self.COLUMN_TEACHER, self.COLUMN_SUBJECT, self.COLUMN_REVIEW]

    def load_sheet(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            reader = csv.reader(StringIO(response.text))
            rows = list(reader)
            if not rows:
                raise GSParserService.InvalidGSheet("Invalid sheet: no data found.")
            return rows
        except requests.exceptions.HTTPError as err:
            raise GSParserService.InaccessibleGSheet(f"Inaccessible sheet: ({err.response.status_code}) {err.response.text}")

    def generate_row_id(self, row):
        """ Creates a unique MD5 hash """
        unique_string = ""
        for column_index in self.columns_ids:
            unique_string += row[column_index].strip() if len(row) > column_index else ""
        return hashlib.md5(unique_string.encode("utf-8")).hexdigest()

    @staticmethod
    def convert_datetime(s: str) -> str:
        """ Converts a datetime string """
        try:
            date_part, time_part = s.split()
            day, month, year = date_part.split('.')
            hour, minute, _ = time_part.split(':')
            return f"{hour}:{minute} {day}.{month}.{year}"
        except ValueError:
            return "00:00 00.00.2023"

    async def parse(self):
        counter = 0
        rows = self.load_sheet()
        processed_ids = await self.database.select_gs_processed()

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

            await self.database.insert_gs_suggestion(row_id, date, teacher, subject, review)
            processed_ids.add(row_id)
            counter += 1

        return counter
