from enum import Enum


class SuggestionStatus(str, Enum):
    delayed = "delayed"
    accepted = "accepted"
    rejected = "rejected"
    spam = "spam"


class SearchType(str, Enum):
    teacher = "teacher"
    subject = "subject"
