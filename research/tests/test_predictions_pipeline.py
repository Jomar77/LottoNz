"""D1 — Integration: engine output matches the Phase A contract."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.prediction_engine import generate_predictions_file
from src.core.predictions_schema import validate_predictions_document

# ---------------------------------------------------------------------------
# Tiny fixture dataset (10 draws, most-recent-first, as results.json stores)
# ---------------------------------------------------------------------------
FIXTURE_DRAWS = [
    {"date": "2024-01-10", "numbers": [3, 7, 14, 22, 31, 38], "powerball": 4},
    {"date": "2024-01-07", "numbers": [1, 9, 16, 25, 33, 40], "powerball": 2},
    {"date": "2024-01-03", "numbers": [5, 11, 18, 27, 35, 39], "powerball": 7},
    {"date": "2023-12-30", "numbers": [2, 8, 15, 23, 32, 37], "powerball": 1},
    {"date": "2023-12-27", "numbers": [4, 10, 17, 24, 30, 36], "powerball": 9},
    {"date": "2023-12-23", "numbers": [6, 12, 19, 26, 34, 40], "powerball": 3},
    {"date": "2023-12-20", "numbers": [1, 13, 20, 28, 31, 38], "powerball": 6},
    {"date": "2023-12-16", "numbers": [7, 14, 21, 29, 33, 39], "powerball": 5},
    {"date": "2023-12-13", "numbers": [2, 10, 22, 27, 35, 40], "powerball": 8},
    {"date": "2023-12-09", "numbers": [3, 11, 18, 25, 32, 37], "powerball": 10},
]


@pytest.fixture()
def fixture_results_json(tmp_path: Path) -> Path:
    p = tmp_path / "results.json"
    p.write_text(json.dumps(FIXTURE_DRAWS), encoding="utf-8")
    return p


def test_engine_output_matches_contract(fixture_results_json: Path, tmp_path: Path) -> None:
    """D1 — engine output on a fixed dataset passes validate_predictions_document."""
    out = tmp_path / "predictions.json"

    generate_predictions_file(
        input_path=fixture_results_json,
        output_path=out,
        seed=42,
        generated_at="2024-01-11T00:00:00Z",
        draw_reference=11,
    )

    assert out.exists(), "predictions.json was not written"
    doc = json.loads(out.read_text(encoding="utf-8"))
    errors = validate_predictions_document(doc)
    assert errors == [], f"Contract violations: {errors}"


def test_engine_contract_has_all_strategies(fixture_results_json: Path, tmp_path: Path) -> None:
    """All five strategy tags must be present in the output."""
    out = tmp_path / "predictions.json"
    generate_predictions_file(
        input_path=fixture_results_json,
        output_path=out,
        seed=1,
        generated_at="2024-01-11T00:00:00Z",
        draw_reference=11,
    )
    doc = json.loads(out.read_text(encoding="utf-8"))
    strategies = {s["strategy"] for s in doc["sets"]}
    expected = {"burst_volatility", "mean_reversion", "momentum_carry", "balanced_hybrid", "lean_bias"}
    assert strategies == expected


def test_engine_generated_at_injected(fixture_results_json: Path, tmp_path: Path) -> None:
    """Injected generated_at propagates verbatim to the output document."""
    out = tmp_path / "predictions.json"
    ts = "2024-06-15T12:00:00Z"
    generate_predictions_file(
        input_path=fixture_results_json,
        output_path=out,
        seed=0,
        generated_at=ts,
        draw_reference=11,
    )
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["generated_at"] == ts
