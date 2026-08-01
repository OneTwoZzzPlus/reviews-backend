from typing import ClassVar

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
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

    def __str__(self):
        return self.name


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

    def __str__(self):
        return f"Отзыв ({len(self.text)})"
