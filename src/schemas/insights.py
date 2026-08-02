from pydantic import BaseModel

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


class Teaching(BaseModel):
    value: TeachingScore
    reason: str


class StudentAttitude(BaseModel):
    value: StudentAttitudeScore
    reason: str


class Organization(BaseModel):
    value: OrganizationScore
    reason: str


class GradingFairness(BaseModel):
    value: GradingFairnessScore
    reason: str


class Strictness(BaseModel):
    value: StrictnessScore
    reason: str


class Workload(BaseModel):
    value: WorkloadScore
    reason: str


class Difficulty(BaseModel):
    value: DifficultyScore
    reason: str


class Scores(BaseModel):
    teaching: Teaching
    student_attitude: StudentAttitude
    organization: Organization
    grading_fairness: GradingFairness
    strictness: Strictness
    workload: Workload
    difficulty: Difficulty


class Rating(BaseModel):
    value: RatingScore
    reason: str


class Confidence(BaseModel):
    value: ConfidenceScore
    reason: str


class Insights(BaseModel):
    summary: str
    pros: list[str]
    cons: list[str]
    highlights: list[str]
    scores: Scores
    rating: Rating
    confidence: Confidence


class InsightsShort(BaseModel):
    summary: str
    pros: list[str]
    cons: list[str]
    highlights: list[str]
    rating: Rating
    confidence: Confidence


class InsightsEssential(BaseModel):
    rating_value: RatingScore
    confidence_value: ConfidenceScore
