"""Deterministic schedule scenario simulation; no model inference is required."""

from dataclasses import dataclass

from domain.risk_calculation import RiskAssessment, assess


@dataclass(frozen=True)
class WhatIfResult:
    equipment_id: int
    before: RiskAssessment
    after: RiskAssessment
    shifted_days: int


def simulate_delay(equipment_id: int, days_variance: int, days_until_due: int, delay_days: int) -> WhatIfResult:
    if delay_days < 0:
        raise ValueError("delay_days must be zero or positive")
    before = assess(days_variance, days_until_due)
    after = assess(days_variance + delay_days, days_until_due)
    return WhatIfResult(equipment_id, before, after, delay_days)
