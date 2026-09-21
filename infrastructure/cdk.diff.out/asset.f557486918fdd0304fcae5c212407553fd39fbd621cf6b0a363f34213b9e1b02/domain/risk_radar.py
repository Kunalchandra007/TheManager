"""Proactive Risk Radar snapshot comparison and deduplication."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskFinding:
    equipment_id: str
    country: str
    risk_type: str
    severity: int
    summary: str
    citations: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str, str]:
        return self.equipment_id, self.country, self.risk_type


def new_or_worsened(current: list[RiskFinding], previous: list[RiskFinding]) -> list[RiskFinding]:
    previous_by_key = {finding.key: finding for finding in previous}
    return [finding for finding in current if finding.key not in previous_by_key or finding.severity > previous_by_key[finding.key].severity]
