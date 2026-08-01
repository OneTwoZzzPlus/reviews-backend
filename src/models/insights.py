from enum import StrEnum
from typing import ClassVar

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class RatingScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    TERRIBLE = "TERRIBLE"
    NEGATIVE = "NEGATIVE"
    MIXED = "MIXED"
    POSITIVE = "POSITIVE"
    EXCELLENT = "EXCELLENT"


class ConfidenceScore(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TeachingScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class StudentAttitudeScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    VERY_NEGATIVE = "VERY_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    VERY_POSITIVE = "VERY_POSITIVE"


class OrganizationScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    CHAOTIC = "CHAOTIC"
    BELOW_AVERAGE = "BELOW_AVERAGE"
    AVERAGE = "AVERAGE"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"


class GradingFairnessScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    VERY_UNFAIR = "VERY_UNFAIR"
    UNFAIR = "UNFAIR"
    MIXED = "MIXED"
    FAIR = "FAIR"
    VERY_FAIR = "VERY_FAIR"


class StrictnessScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    VERY_LENIENT = "VERY_LENIENT"
    LENIENT = "LENIENT"
    MODERATE = "MODERATE"
    STRICT = "STRICT"
    VERY_STRICT = "VERY_STRICT"


class WorkloadScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    VERY_LIGHT = "VERY_LIGHT"
    LIGHT = "LIGHT"
    MODERATE = "MODERATE"
    HEAVY = "HEAVY"
    VERY_HEAVY = "VERY_HEAVY"


class DifficultyScore(StrEnum):
    UNKNOWN = "UNKNOWN"
    VERY_EASY = "VERY_EASY"
    EASY = "EASY"
    MODERATE = "MODERATE"
    HARD = "HARD"
    VERY_HARD = "VERY_HARD"


class Insights(Base):
    __tablename__ = "insights"
    __table_args__: ClassVar[dict] = {"schema": "public"}

    id: Mapped[int] = mapped_column(ForeignKey("public.teacher.id"), primary_key=True)
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
