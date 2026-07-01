"""TDD tests for GET /predict/strategies/weighted — must fail before implementation."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


def test_strategies_weighted_returns_200(client):
    r = client.get("/predict/strategies/weighted")
    assert r.status_code == 200


def test_strategies_weighted_returns_five_sets_by_default(client):
    body = client.get("/predict/strategies/weighted").json()
    assert len(body["sets"]) == 5


def test_strategies_weighted_response_shape(client):
    body = client.get("/predict/strategies/weighted").json()
    assert "draw_reference" in body
    assert "generated_at" in body
    assert "sets" in body
    assert "metadata" in body
    s = body["sets"][0]
    assert set(s.keys()) >= {"id", "strategy", "main_numbers", "powerball", "rationale", "constraint_satisfied"}
    assert len(s["main_numbers"]) == 6
    assert all(1 <= n <= 40 for n in s["main_numbers"])
    assert 1 <= s["powerball"] <= 10
    assert isinstance(s["constraint_satisfied"], bool)


def test_strategies_weighted_known_strategy_names(client):
    body = client.get("/predict/strategies/weighted").json()
    names = {s["strategy"] for s in body["sets"]}
    expected = {"burst_volatility", "mean_reversion", "momentum_carry", "balanced_hybrid", "lean_bias"}
    assert names == expected


def test_strategies_weighted_enforcement_flag_in_applied_filters(client):
    body = client.get("/predict/strategies/weighted").json()
    filters = body["metadata"]["applied_filters"]
    assert filters.get("enforcement") == "active"


def test_strategies_weighted_applied_filters_reflect_params(client):
    body = client.get("/predict/strategies/weighted?lean=right&spread=wide&consecutive=true").json()
    filters = body["metadata"]["applied_filters"]
    assert filters["lean"] == "right"
    assert filters["spread"] == "wide"
    assert filters["consecutive"] is True
    assert filters["enforcement"] == "active"


def test_strategies_weighted_lean_right_respected(client):
    body = client.get("/predict/strategies/weighted?lean=right").json()
    for s in body["sets"]:
        if s["constraint_satisfied"]:
            right_count = sum(1 for n in s["main_numbers"] if n > 20)
            assert right_count >= 4, (
                f"strategy={s['strategy']}: constraint_satisfied=True but right_count={right_count}: {s['main_numbers']}"
            )


def test_strategies_weighted_lean_left_respected(client):
    body = client.get("/predict/strategies/weighted?lean=left").json()
    for s in body["sets"]:
        if s["constraint_satisfied"]:
            left_count = sum(1 for n in s["main_numbers"] if n <= 20)
            assert left_count >= 4, (
                f"strategy={s['strategy']}: constraint_satisfied=True but left_count={left_count}: {s['main_numbers']}"
            )


def test_strategies_weighted_spread_wide_respected(client):
    body = client.get("/predict/strategies/weighted?spread=wide").json()
    for s in body["sets"]:
        if s["constraint_satisfied"]:
            nums = s["main_numbers"]
            assert max(nums) - min(nums) >= 20, (
                f"strategy={s['strategy']}: constraint_satisfied=True but span={max(nums)-min(nums)}: {nums}"
            )


def test_strategies_weighted_spread_tight_respected(client):
    body = client.get("/predict/strategies/weighted?spread=tight").json()
    for s in body["sets"]:
        if s["constraint_satisfied"]:
            nums = s["main_numbers"]
            assert max(nums) - min(nums) <= 20, (
                f"strategy={s['strategy']}: constraint_satisfied=True but span={max(nums)-min(nums)}: {nums}"
            )


def test_strategies_weighted_consecutive_true_respected(client):
    body = client.get("/predict/strategies/weighted?consecutive=true").json()
    for s in body["sets"]:
        if s["constraint_satisfied"]:
            nums = sorted(s["main_numbers"])
            has_consec = any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1))
            assert has_consec, (
                f"strategy={s['strategy']}: constraint_satisfied=True but no consecutive pair: {nums}"
            )


def test_strategies_weighted_consecutive_false_respected(client):
    body = client.get("/predict/strategies/weighted?consecutive=false").json()
    for s in body["sets"]:
        if s["constraint_satisfied"]:
            nums = sorted(s["main_numbers"])
            has_consec = any(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1))
            assert not has_consec, (
                f"strategy={s['strategy']}: constraint_satisfied=True but consecutive pair found: {nums}"
            )


def test_strategies_weighted_seed_reproducible(client):
    r1 = client.get("/predict/strategies/weighted?seed=42").json()
    r2 = client.get("/predict/strategies/weighted?seed=42").json()
    assert r1["sets"] == r2["sets"]


def test_strategies_weighted_date_from_filters_draws(client):
    r_all = client.get("/predict/strategies/weighted").json()
    r_recent = client.get("/predict/strategies/weighted?date_from=2024-01-01").json()
    assert r_recent["metadata"]["total_draws_analyzed"] < r_all["metadata"]["total_draws_analyzed"]


def test_strategies_weighted_date_from_too_recent_returns_422(client):
    r = client.get("/predict/strategies/weighted?date_from=2026-05-01")
    assert r.status_code == 422


def test_strategies_weighted_date_from_invalid_format_returns_422(client):
    r = client.get("/predict/strategies/weighted?date_from=not-a-date")
    assert r.status_code == 422


def test_strategies_weighted_count_param(client):
    body = client.get("/predict/strategies/weighted?count=3").json()
    assert len(body["sets"]) == 3


def test_strategies_weighted_count_exceeds_max_returns_422(client):
    r = client.get("/predict/strategies/weighted?count=6")
    assert r.status_code == 422


def test_strategies_weighted_lean_override_affects_lean_bias(client):
    body = client.get("/predict/strategies/weighted?lean=right").json()
    lean_set = next(s for s in body["sets"] if s["strategy"] == "lean_bias")
    right_count = sum(1 for n in lean_set["main_numbers"] if n > 20)
    assert right_count >= 4, f"lean=right lean_bias should favour >20: {lean_set['main_numbers']}"
