from typing import ClassVar

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from enums import SuggestionStatus
from models.schemas import CONTENT_SCHEMA, GSPARSER_SCHEMA, PUBLIC_SCHEMA


class Moderator(Base):
    __tablename__ = "moderator"
    __table_args__: ClassVar[dict] = {"schema": CONTENT_SCHEMA}

    isu: Mapped[int] = mapped_column(primary_key=True)
    access: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)


class CommentKarma(Base):
    __tablename__ = "comment_karma"
    __table_args__: ClassVar[dict] = {"schema": CONTENT_SCHEMA}

    isu: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey(f"{PUBLIC_SCHEMA}.comment.id"), primary_key=True
    )
    user_karma: Mapped[int] = mapped_column()


class TeacherRating(Base):
    __tablename__ = "teacher_rating"
    __table_args__: ClassVar[dict] = {"schema": CONTENT_SCHEMA}

    isu: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey(f"{PUBLIC_SCHEMA}.teacher.id"), primary_key=True
    )
    user_rating: Mapped[int] = mapped_column()


class Suggestion(Base):
    __tablename__ = "suggestion"
    __table_args__: ClassVar[dict] = {"schema": CONTENT_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(
            SuggestionStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=SuggestionStatus.delayed,
    )
    user_isu: Mapped[int | None] = mapped_column(default=None)
    moderator_isu: Mapped[int | None] = mapped_column(default=None)
    text: Mapped[str] = mapped_column(String)
    teacher_id: Mapped[int | None] = mapped_column(default=None)
    teacher_title: Mapped[str | None] = mapped_column(String, default=None)
    subject_id: Mapped[int | None] = mapped_column(default=None)
    subject_title: Mapped[str | None] = mapped_column(String, default=None)
    subs_id: Mapped[str | None] = mapped_column(String, default=None)
    subs_title: Mapped[str | None] = mapped_column(String, default=None)
    comment_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{PUBLIC_SCHEMA}.comment.id", ondelete="CASCADE"), default=None
    )
    source_id: Mapped[int] = mapped_column(default=1)
    date: Mapped[str] = mapped_column(String)


class Processed(Base):
    __tablename__ = "processed"
    __table_args__: ClassVar[dict] = {"schema": GSPARSER_SCHEMA}

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
