from typing import ClassVar

from sqlalchemy import ForeignKey, String, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from core.database import Base
from models.content import CommentKarma, TeacherRating
from models.schemas import PUBLIC_SCHEMA


class Source(Base):
    __tablename__ = "source"
    __table_args__: ClassVar[dict] = {"schema": PUBLIC_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    link: Mapped[str | None] = mapped_column(String, default=None)

    def __str__(self):
        return self.title


class Subject(Base):
    __tablename__ = "subject"
    __table_args__: ClassVar[dict] = {"schema": PUBLIC_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)

    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        secondary="public.relationst",
        back_populates="subjects",
    )

    def __str__(self):
        return self.title


class Teacher(Base):
    __tablename__ = "teacher"
    __table_args__: ClassVar[dict] = {"schema": PUBLIC_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    subjects: Mapped[list["Subject"]] = relationship(
        "Subject",
        secondary="public.relationst",
        back_populates="teachers",
    )
    summaries: Mapped[list["Summary"]] = relationship(
        "Summary", back_populates="teacher"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="teacher"
    )

    rating: Mapped[float] = column_property(
        select(func.coalesce(func.round(func.avg(TeacherRating.user_rating), 1), 0.0))
        .where(TeacherRating.teacher_id == id)
        .correlate_except(TeacherRating)
        .scalar_subquery()
    )
    ratings: Mapped[list["TeacherRating"]] = relationship()

    @property
    def user_rating(self) -> int | None:
        return self.ratings[0].user_rating if self.ratings else None

    def __str__(self):
        return self.name

    @property
    def subjects_count(self):
        return len(self.subjects)

    @property
    def summaries_count(self):
        return len(self.summaries)


class Summary(Base):
    __tablename__ = "summary"
    __table_args__: ClassVar[dict] = {"schema": PUBLIC_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    value: Mapped[str | None] = mapped_column(String, default=None)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("public.teacher.id"))
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="summaries")

    def __str__(self):
        return f"{self.title}: {self.value}"


class RelationST(Base):
    __tablename__ = "relationst"
    __table_args__: ClassVar[dict] = {"schema": PUBLIC_SCHEMA}

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("public.subject.id"), primary_key=True
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("public.teacher.id"), primary_key=True
    )


class Comment(Base):
    __tablename__ = "comment"
    __table_args__: ClassVar[dict] = {"schema": PUBLIC_SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(String)

    source_id: Mapped[int | None] = mapped_column(ForeignKey("public.source.id"))
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("public.subject.id"))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("public.teacher.id"))

    source: Mapped[Source | None] = relationship("Source")
    subject: Mapped[Subject | None] = relationship("Subject")
    teacher: Mapped[Teacher | None] = relationship("Teacher", back_populates="comments")

    karma: Mapped[int] = column_property(
        select(func.coalesce(func.sum(CommentKarma.user_karma), 0))
        .where(CommentKarma.comment_id == id)
        .correlate_except(CommentKarma)
        .scalar_subquery()
    )
    karmas: Mapped[list["CommentKarma"]] = relationship()

    @property
    def user_karma(self) -> int | None:
        return self.karmas[0].user_karma if self.karmas else None

    def __str__(self):
        return f"Комментарий {self.id} ({len(self.text)} символов)"
