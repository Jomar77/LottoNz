"""TDD tests for GET /predict/strategies — must fail before implementation."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


def test_strategies_returns_200(client):
    r = client.get("/predict/strategies")
    assert r.status_code == 200


def test_strategies_returns_five_sets_by_default(client):
    body = r = client.get("/predict/strategies").json()
    assert len(body["sets"]) == 5


def test_strategies_response_shape(client):
    body = client.get("/predict/strategies").json()
    assert "draw_reference" in body
    assert "generated_at" in body
    assert "sets" in body
    assert "metadata" in body
    s = body["sets"][0]
    assert set(s.keys()) >= {"id", "strategy", "main_numbers", "powerball", "rationale"}
    assert len(s["main_numbers"]) == 6
    assert all(1 <= n <= 40 for n in s["main_numbers"])
    assert 1 <= s["powerball"] <= 10


def test_strategies_known_strategy_names(client):
    body = client.get("/predict/strategies").json()
    names = {s["strategy"] for s in body["sets"]}
    expected = {"burst_volatility", "mean_reversion", "momentum_carry", "balanced_hybrid", "lean_bias"}
    assert names == expected


def test_strategies_lean_override(client):
    body = client.get("/predict/strategies?lean=right").json()
    lean_set = next(s for s in body["sets"] if s["strategy"] == "lean_bias")
    right_count = sum(1 for n in lean_set["main_numbers"] if n > 20)
    assert right_count >= 4, f"lean=right lean_bias should favor >20: {lean_set['main_numbers']}"


def test_strategies_date_from_filters_draws(client):
    r_all = client.get("/predict/strategies").json()
    r_recent = client.get("/predict/strategies?date_from=2024-01-01").json()
    assert r_recent["metadata"]["total_draws_analyzed"] < r_all["metadata"]["total_draws_analyzed"]


def test_strategies_date_from_too_recent_returns_422(client):
    r = client.get("/predict/strategies?date_from=2026-05-01")
    assert r.status_code == 422


def test_strategies_date_from_invalid_format_returns_422(client):
    r = client.get("/predict/strategies?date_from=not-a-date")
    assert r.status_code == 422


def test_strategies_applied_filters_in_metadata(client):
    body = client.get("/predict/strategies?date_from=2020-01-01&lean=left").json()
    filters = body["metadata"]["applied_filters"]
    assert filters["date_from"] == "2020-01-01"
    assert filters["lean"] == "left"


def test_strategies_seed_reproducible(client):
    r1 = client.get("/predict/strategies?seed=42").json()
    r2 = client.get("/predict/strategies?seed=42").json()
    assert r1["sets"] == r2["sets"]


def test_strategies_different_from_static_predictions(client):
    """Seeded API call must not produce the same sets as the unseed static generation."""
    import json
    from pathlib import Path
    static_path = Path(__file__).parents[2] / "Frontend" / "public" / "predictions.json"
    if not static_path.exists():
        pytest.skip("predictions.json not present — skipping static comparison")
    static = json.loads(static_path.read_text())
    static_mains = [tuple(s["main_numbers"]) for s in static["sets"]]

    api_body = client.get("/predict/strategies?seed=999").json()
    api_mains = [tuple(s["main_numbers"]) for s in api_body["sets"]]
    assert api_mains != static_mains, "API with seed=999 should not match static predictions.json"


def test_strategies_count_param(client):
    body = client.get("/predict/strategies?count=3").json()
    assert len(body["sets"]) == 3


def test_strategies_count_exceeds_max_returns_422(client):
    r = client.get("/predict/strategies?count=6")
    assert r.status_code == 422
