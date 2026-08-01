from pydantic import BaseModel

from enums import SearchType


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


class TeacherResponse(TeacherSchema):
    summaries: list[SummarySchema]
    comments: list[CommentSchema]


class SubjectResponse(SubjectSchema):
    teachers: list[TeacherResponse]


class SearchItem(BaseModel):
    id: int
    title: str
    type: SearchType


class SearchResponse(BaseModel):
    results: list[SearchItem]


class InputItem(BaseModel):
    id: int | None = None
    title: str | None = None


class SuggestionAddRequest(BaseModel):
    teacher: InputItem
    subject: InputItem
    subs: list[InputItem]
    text: str


class SuggestionAddResponse(BaseModel):
    id: int


class GSParserResponse(BaseModel):
    count: int
