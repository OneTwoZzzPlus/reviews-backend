from enum import StrEnum


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
