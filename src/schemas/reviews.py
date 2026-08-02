from pydantic import BaseModel

from enums.reviews import SearchType
from schemas.insights import Insights, InsightsEssential, InsightsShort


class SubjectSchema(BaseModel):
    id: int | None = None
    title: str


class TeacherSchema(BaseModel):
    id: int
    name: str


class SourceSchema(BaseModel):
    id: int | None = None
    title: str
    link: str | None = None


class CommentSchema(BaseModel):
    id: int
    date: str
    text: str
    subject: SubjectSchema
    source: SourceSchema


class SummarySchema(BaseModel):
    id: int | None = None
    title: str
    value: str


# /teacher


class TeacherResponse(TeacherSchema):
    insights: Insights | None = None
    summaries: list[SummarySchema]
    comments: list[CommentSchema]


#  /subject


class TeacherShort(TeacherSchema):
    insights: InsightsShort | None = None
    alt: str | None = None


class SubjectResponse(SubjectSchema):
    teachers: list[TeacherShort]


# /registry


class RegistryResponse(BaseModel):
    original: dict[str, int]  # original name -> id
    normalized: dict[str, int]  # normalized name -> id
    insights: dict[int, InsightsEssential]  # id -> insights


# /search


class SearchItem(BaseModel):
    id: int
    title: str
    type: SearchType


class SearchResponse(BaseModel):
    results: list[SearchItem]


# /suggestion


class InputItem(BaseModel):
    id: int | None = None
    title: str | None = None


class SuggestionRequest(BaseModel):
    teacher: InputItem
    subject: InputItem
    subs: list[InputItem]
    text: str


class SuggestionResponse(BaseModel):
    id: int
