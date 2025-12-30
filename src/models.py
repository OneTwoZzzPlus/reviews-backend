from pydantic import BaseModel
from enum import Enum


class Subject(BaseModel):
    id: int | None = None
    title: str


class Teacher(BaseModel):
    id: int
    name: str
    rating: float


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


class Summary(BaseModel):
    id: int | None = None
    title: str
    value: str


class TeacherResponse(Teacher, BaseModel):
    summaries: list[Summary]
    comments: list[Comment]


class SubjectResponse(Subject, BaseModel):
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
