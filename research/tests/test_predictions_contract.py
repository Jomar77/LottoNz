"""Contract tests for the predictions.json document (Phase A1/A2).

These lock the single-source-of-truth schema that both the research engine
(Phase B) and the frontend display (Phase C) code against. See
``research/docs/predictions_contract.md`` for the human-readable contract.
"""

import copy
import json
from pathlib import Path

import pytest

from src.core.predictions_schema import validate_predictions_document

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "research" / "tests" / "fixtures" / "predictions.sample.json"
FRONTEND_FIXTURE_PATH = REPO_ROOT / "frontend" / "public" / "predictions.sample.json"

STRATEGIES = [
    "burst_volatility",
    "mean_reversion",
    "momentum_carry",
    "balanced_hybrid",
    "lean_bias",
]


def canonical_document() -> dict:
    """A minimal, valid predictions document used as the test baseline."""
    sets = [
        {
            "id": 1,
            "strategy": "burst_volatility",
            "main_numbers": [2, 5, 7, 11, 28, 35],
            "powerball": 3,
            "rationale": "High-CV numbers with recent clustering behaviour.",
        },
        {
            "id": 2,
            "strategy": "mean_reversion",
            "main_numbers": [8, 14, 23, 36, 39, 40],
            "powerball": 7,
            "rationale": "Numbers below mean frequency, due for regression.",
        },
        {
            "id": 3,
            "strategy": "momentum_carry",
            "main_numbers": [1, 9, 15, 22, 30, 33],
            "powerball": 5,
            "rationale": "Hot numbers recurring in the recent window.",
        },
        {
            "id": 4,
            "strategy": "balanced_hybrid",
            "main_numbers": [4, 12, 19, 25, 31, 38],
            "powerball": 2,
            "rationale": "Balanced mix of hot, cold and neutral numbers.",
        },
        {
            "id": 5,
            "strategy": "lean_bias",
            "main_numbers": [3, 6, 10, 13, 17, 20],
            "powerball": 9,
            "rationale": "Left-leaning set from recent draws.",
        },
    ]
    return {
        "draw_reference": 1875,
        "generated_at": "2026-06-27T12:00:00Z",
        "sets": sets,
        "metadata": {
            "total_draws_analyzed": 1874,
            "date_range": "2001-02-17 to 2026-05-09",
            "uniformity_confirmed": True,
            "chi_square_p_main": 0.585,
            "chi_square_p_powerball": 0.178,
        },
    }


def test_canonical_document_is_valid():
    assert validate_predictions_document(canonical_document()) == []


def test_returns_list_of_strings():
    doc = canonical_document()
    doc["sets"][0]["powerball"] = 99
    errors = validate_predictions_document(doc)
    assert isinstance(errors, list)
    assert all(isinstance(e, str) for e in errors)
    assert errors  # non-empty


# --- Top-level structure ---------------------------------------------------

@pytest.mark.parametrize("missing_key", ["draw_reference", "generated_at", "sets", "metadata"])
def test_missing_top_level_key_fails(missing_key):
    doc = canonical_document()
    del doc[missing_key]
    assert validate_predictions_document(doc) != []


def test_non_dict_document_fails():
    assert validate_predictions_document([]) != []


def test_draw_reference_must_be_int():
    doc = canonical_document()
    doc["draw_reference"] = "1875"
    assert validate_predictions_document(doc) != []


def test_generated_at_must_be_iso_utc():
    doc = canonical_document()
    doc["generated_at"] = "not-a-timestamp"
    assert validate_predictions_document(doc) != []


# --- Set-level rules -------------------------------------------------------

def test_out_of_range_powerball_fails():
    doc = canonical_document()
    doc["sets"][0]["powerball"] = 11
    assert validate_predictions_document(doc) != []

    doc2 = canonical_document()
    doc2["sets"][0]["powerball"] = 0
    assert validate_predictions_document(doc2) != []


def test_five_number_main_set_fails():
    doc = canonical_document()
    doc["sets"][0]["main_numbers"] = [2, 5, 7, 11, 28]
    assert validate_predictions_document(doc) != []


def test_unsorted_main_set_fails():
    doc = canonical_document()
    doc["sets"][0]["main_numbers"] = [35, 5, 7, 11, 28, 2]
    assert validate_predictions_document(doc) != []


def test_duplicate_main_numbers_fail():
    doc = canonical_document()
    doc["sets"][0]["main_numbers"] = [2, 2, 7, 11, 28, 35]
    assert validate_predictions_document(doc) != []


def test_main_number_out_of_range_fails():
    doc = canonical_document()
    doc["sets"][0]["main_numbers"] = [0, 5, 7, 11, 28, 35]
    assert validate_predictions_document(doc) != []

    doc2 = canonical_document()
    doc2["sets"][0]["main_numbers"] = [2, 5, 7, 11, 28, 41]
    assert validate_predictions_document(doc2) != []


def test_unknown_strategy_fails():
    doc = canonical_document()
    doc["sets"][0]["strategy"] = "lucky_dip"
    assert validate_predictions_document(doc) != []


def test_empty_rationale_fails():
    doc = canonical_document()
    doc["sets"][0]["rationale"] = ""
    assert validate_predictions_document(doc) != []


def test_non_int_id_fails():
    doc = canonical_document()
    doc["sets"][0]["id"] = "1"
    assert validate_predictions_document(doc) != []


def test_empty_sets_fails():
    doc = canonical_document()
    doc["sets"] = []
    assert validate_predictions_document(doc) != []


# --- Metadata rules --------------------------------------------------------

@pytest.mark.parametrize(
    "key",
    [
        "total_draws_analyzed",
        "date_range",
        "uniformity_confirmed",
        "chi_square_p_main",
        "chi_square_p_powerball",
    ],
)
def test_missing_metadata_key_fails(key):
    doc = canonical_document()
    del doc["metadata"][key]
    assert validate_predictions_document(doc) != []


def test_uniformity_confirmed_must_be_bool():
    doc = canonical_document()
    doc["metadata"]["uniformity_confirmed"] = "true"
    assert validate_predictions_document(doc) != []


def test_chi_square_p_must_be_float_in_range():
    doc = canonical_document()
    doc["metadata"]["chi_square_p_main"] = 1.5
    assert validate_predictions_document(doc) != []


# --- A2: shared fixture ----------------------------------------------------

def test_fixture_file_exists_and_is_valid():
    assert FIXTURE_PATH.exists(), f"missing research fixture: {FIXTURE_PATH}"
    doc = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert validate_predictions_document(doc) == []


def test_fixture_has_all_five_strategies():
    doc = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    strategies = [s["strategy"] for s in doc["sets"]]
    assert set(strategies) == set(STRATEGIES)


def test_frontend_fixture_is_byte_identical():
    assert FRONTEND_FIXTURE_PATH.exists(), f"missing frontend fixture: {FRONTEND_FIXTURE_PATH}"
    assert FIXTURE_PATH.read_bytes() == FRONTEND_FIXTURE_PATH.read_bytes()
