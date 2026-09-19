"""Schedule-risk calculation shared by current and AWS migration paths."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskAssessment:
    percentage: float
    flag: str
    points: int


def calculate_percentage(days_variance: int, days_until_due: int) -> float:
    """Return the current risk percentage; overdue milestones remain 100%."""
    if days_until_due <= 0:
        return 100.0
    return round(abs(days_variance / days_until_due * 100), 2)


def categorize(percentage: float) -> RiskAssessment:
    """Apply the invariant Low <5, Medium <15, High >=15 thresholds."""
    if percentage < 5:
        return RiskAssessment(percentage, "Low Risk", 1)
    if percentage < 15:
        return RiskAssessment(percentage, "Medium Risk", 3)
    return RiskAssessment(percentage, "High Risk", 5)


def assess(days_variance: int, days_until_due: int) -> RiskAssessment:
    """Calculate and categorize one planned-versus-equipment variance."""
    return categorize(calculate_percentage(days_variance, days_until_due))
