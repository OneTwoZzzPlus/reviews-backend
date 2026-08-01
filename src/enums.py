from enum import StrEnum


class SuggestionStatus(StrEnum):
    delayed = "delayed"
    accepted = "accepted"
    rejected = "rejected"


class SearchType(StrEnum):
    teacher = "teacher"
    subject = "subject"
