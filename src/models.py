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
    delayed = 'delayed'
    accepted = 'accepted'
    rejected = 'rejected'
    spam = 'spam'


class SuggestionAddRequest(BaseModel):
    teacher: InputItem
    subject: InputItem
    subs: list[InputItem]
    text: str


class SuggestionAddResponse(BaseModel):
    id: int


class SuggestionResponse(BaseModel):
    id: int
    status: SuggestionStatus
    user_isu: int | None = None
    moderator_isu: int | None = None
    text: str
    teacher: InputItem
    subject: InputItem
    subs: list[InputItem]
    comment_id: int | None = None


class SuggestionItem(BaseModel):
    id: int
    status: SuggestionStatus
    title: str


class SuggestionListResponse(BaseModel):
    items: list[SuggestionItem]


class CommitedItem(BaseModel):
    id: int | None = None
    title: str | None = None


class SuggestionCommitRequest(BaseModel):
    teacher: CommitedItem
    subject: CommitedItem
    subs: list[CommitedItem]
    text: str


class SuggestionCommitResponse(BaseModel):
    comment_id: int | None = None


class SuggestionCancelRequest(BaseModel):
    status: SuggestionStatus = SuggestionStatus.rejected


class SuggestionCancelResponse(BaseModel):
    status: SuggestionStatus
