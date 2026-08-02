from typing import ClassVar

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from enums.insights import (
    ConfidenceScore,
    DifficultyScore,
    GradingFairnessScore,
    OrganizationScore,
    RatingScore,
    StrictnessScore,
    StudentAttitudeScore,
    TeachingScore,
    WorkloadScore,
)


class Insights(Base):
    __tablename__ = "insights"
    __table_args__: ClassVar[dict] = {"schema": "public"}

    id: Mapped[int] = mapped_column(ForeignKey("public.teacher.id"), primary_key=True)
    comments_count: Mapped[int] = mapped_column(default=0)

    summary: Mapped[str] = mapped_column(String)
    pros: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    cons: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    highlights: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    teaching_value: Mapped[TeachingScore] = mapped_column(
        Enum(TeachingScore, native_enum=False, length=16)
    )
    teaching_reason: Mapped[str] = mapped_column(String)

    student_attitude_value: Mapped[StudentAttitudeScore] = mapped_column(
        Enum(StudentAttitudeScore, native_enum=False, length=16)
    )
    student_attitude_reason: Mapped[str] = mapped_column(String)

    organization_value: Mapped[OrganizationScore] = mapped_column(
        Enum(OrganizationScore, native_enum=False, length=16)
    )
    organization_reason: Mapped[str] = mapped_column(String)

    grading_fairness_value: Mapped[GradingFairnessScore] = mapped_column(
        Enum(GradingFairnessScore, native_enum=False, length=16)
    )
    grading_fairness_reason: Mapped[str] = mapped_column(String)

    strictness_value: Mapped[StrictnessScore] = mapped_column(
        Enum(StrictnessScore, native_enum=False, length=16)
    )
    strictness_reason: Mapped[str] = mapped_column(String)

    workload_value: Mapped[WorkloadScore] = mapped_column(
        Enum(WorkloadScore, native_enum=False, length=16)
    )
    workload_reason: Mapped[str] = mapped_column(String)

    difficulty_value: Mapped[DifficultyScore] = mapped_column(
        Enum(DifficultyScore, native_enum=False, length=16)
    )
    difficulty_reason: Mapped[str] = mapped_column(String)

    rating_value: Mapped[RatingScore] = mapped_column(
        Enum(RatingScore, native_enum=False, length=16)
    )
    rating_reason: Mapped[str] = mapped_column(String)

    confidence_value: Mapped[ConfidenceScore] = mapped_column(
        Enum(ConfidenceScore, native_enum=False, length=16)
    )
    confidence_reason: Mapped[str] = mapped_column(String)

    def __str__(self):
        return f"Insight {self.id}"
