"""Validate that the migration baseline fixture remains complete and well-formed."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
fixture = json.loads((ROOT / "docs" / "evaluation" / "baseline-scenarios.json").read_text(encoding="utf-8"))
scenarios = fixture["scenarios"]
assert len(scenarios) >= 15, "At least 15 golden scenarios are required"
assert fixture["invariants"]["thresholds"] == {"low_lt": 5, "medium_lt": 15, "high_gte": 15}
assert all(scenario.get("question") and scenario.get("expected_capabilities") for scenario in scenarios)
print(f"Evaluation fixture valid: {len(scenarios)} scenarios, risk thresholds preserved.")
