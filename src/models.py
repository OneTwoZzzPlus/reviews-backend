from pydantic import BaseModel
from enum import Enum
from typing import Annotated
from fastapi import Query


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


class TeacherRateRequest(BaseModel):
    user_rating: Annotated[int, Query(ge=1, le=5)]


class CommentKarmaResponse(BaseModel):
    karma: int
    user_karma: int


class CommentKarmaRequest(BaseModel):
    user_karma: Annotated[int, Query(ge=-1, le=1)]


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    refresh_token: str
    access_token: str


class ModeratorResponse(BaseModel):
    access: bool


class InputItem(BaseModel):
    id: int | None = None
    title: str | None = None


class SuggestionStatus(str, Enum):
    check = 'check'
    delayed = 'delayed'
    accepted = 'accepted'
    rejected = 'rejected'


class SuggestionAddRequest(BaseModel):
    teacher: InputItem
    subject: InputItem
    subs: list[InputItem]
    comment: str


class SuggestionAddResponse(BaseModel):
    id: int
