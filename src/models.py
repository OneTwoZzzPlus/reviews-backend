from pydantic import BaseModel
from enum import Enum


class Subject(BaseModel):
    id: int | None = None
    title: str


class Teacher(BaseModel):
    id: int
    name: str
    rating: float
    user_rating: int | None = None


class Source(BaseModel):
    id: int | None = None
    title: str
    link: str


class Comment(BaseModel):
    id: int
    date: str
    text: str
    subject: Subject
    source: Source
    karma: int
    user_karma: int | None = None


class Summary(BaseModel):
    id: int | None = None
    title: str
    value: str


class TeacherResponse(Teacher):
    summaries: list[Summary]
    comments: list[Comment]


class SubjectResponse(Subject):
    teachers: list[TeacherResponse]


class SearchType(str, Enum):
    teacher = 'teacher'
    subject = 'subject'


class SearchItem(BaseModel):
    id: int
    title: str
    type: SearchType


class SearchResponse(BaseModel):
    results: list[SearchItem]


class TeacherRateResponse(BaseModel):
    rating: float
    user_rating: int


class CommentKarmaResponse(BaseModel):
    karma: int
    user_karma: int
