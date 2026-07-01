"""TDD tests for GET /predict/weighted — must fail before implementation."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    return TestClient(app)


def test_weighted_returns_200(client):
    r = client.get("/predict/weighted")
    assert r.status_code == 200


def test_weighted_default_count_is_one(client):
    r = client.get("/predict/weighted")
    body = r.json()
    assert len(body["tickets"]) == 1


def test_weighted_count_param(client):
    r = client.get("/predict/weighted?count=3")
    assert len(r.json()["tickets"]) == 3


def test_weighted_ticket_shape(client):
    r = client.get("/predict/weighted")
    ticket = r.json()["tickets"][0]
    assert set(ticket.keys()) >= {"main_numbers", "powerball", "spread", "lean", "has_consecutive"}
    assert len(ticket["main_numbers"]) == 6
    assert all(1 <= n <= 40 for n in ticket["main_numbers"])
    assert 1 <= ticket["powerball"] <= 10


def test_weighted_lean_left(client):
    r = client.get("/predict/weighted?count=10&lean=left&seed=42")
    tickets = r.json()["tickets"]
    for t in tickets:
        left = sum(1 for n in t["main_numbers"] if n <= 20)
        assert left >= 4, f"lean=left should have >=4 numbers <=20, got {left}"


def test_weighted_lean_right(client):
    r = client.get("/predict/weighted?count=10&lean=right&seed=42")
    tickets = r.json()["tickets"]
    for t in tickets:
        right = sum(1 for n in t["main_numbers"] if n > 20)
        assert right >= 4, f"lean=right should have >=4 numbers >20, got {right}"


def test_weighted_spread_tight(client):
    r = client.get("/predict/weighted?count=5&spread=tight&seed=1")
    for t in r.json()["tickets"]:
        nums = t["main_numbers"]
        assert max(nums) - min(nums) <= 20, f"tight spread exceeded: {nums}"


def test_weighted_spread_wide(client):
    r = client.get("/predict/weighted?count=5&spread=wide&seed=1")
    for t in r.json()["tickets"]:
        nums = t["main_numbers"]
        assert max(nums) - min(nums) >= 20, f"wide spread too narrow: {nums}"


def test_weighted_consecutive_true(client):
    r = client.get("/predict/weighted?count=5&consecutive=true&seed=7")
    for t in r.json()["tickets"]:
        nums = sorted(t["main_numbers"])
        has_consec = any(nums[i+1] - nums[i] == 1 for i in range(len(nums)-1))
        assert has_consec, f"consecutive=true but no pair: {nums}"


def test_weighted_consecutive_false(client):
    r = client.get("/predict/weighted?count=5&consecutive=false&seed=7")
    for t in r.json()["tickets"]:
        nums = sorted(t["main_numbers"])
        has_consec = any(nums[i+1] - nums[i] == 1 for i in range(len(nums)-1))
        assert not has_consec, f"consecutive=false but pair found: {nums}"


def test_weighted_seed_reproducible(client):
    r1 = client.get("/predict/weighted?count=2&seed=99")
    r2 = client.get("/predict/weighted?count=2&seed=99")
    assert r1.json()["tickets"] == r2.json()["tickets"]


def test_weighted_count_too_large_returns_422(client):
    r = client.get("/predict/weighted?count=21")
    assert r.status_code == 422


def test_weighted_count_zero_returns_422(client):
    r = client.get("/predict/weighted?count=0")
    assert r.status_code == 422


def test_weighted_invalid_lean_returns_422(client):
    r = client.get("/predict/weighted?lean=banana")
    assert r.status_code == 422


def test_weighted_metadata_present(client):
    r = client.get("/predict/weighted")
    body = r.json()
    assert "metadata" in body
    assert body["metadata"]["total_draws_analyzed"] > 0
