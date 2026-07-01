"""D2/D3/D4 — refresh_data orchestrator tests."""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Tiny results fixture (10 draws)
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
def tmp_results(tmp_path: Path) -> Path:
    p = tmp_path / "results.json"
    p.write_text(json.dumps(FIXTURE_DRAWS), encoding="utf-8")
    return p


@pytest.fixture()
def tmp_predictions(tmp_path: Path) -> Path:
    return tmp_path / "predictions.json"


# ---------------------------------------------------------------------------
# D2 — refresh_data writes both files in the right order
# ---------------------------------------------------------------------------

def test_refresh_data_writes_predictions(tmp_results: Path, tmp_predictions: Path) -> None:
    """D2(b) — refresh_data writes predictions.json when given injectable paths."""
    from scripts.refresh_data import refresh_data

    refresh_data(results_path=tmp_results, predictions_path=tmp_predictions)

    assert tmp_predictions.exists(), "predictions.json was not written"


def test_refresh_data_predictions_mtime_gte_results(tmp_results: Path, tmp_predictions: Path) -> None:
    """D2(c) — predictions.json mtime >= results.json mtime."""
    from scripts.refresh_data import refresh_data

    refresh_data(results_path=tmp_results, predictions_path=tmp_predictions)

    r_mtime = tmp_results.stat().st_mtime
    p_mtime = tmp_predictions.stat().st_mtime
    assert p_mtime >= r_mtime, "predictions.json older than results.json"


def test_refresh_data_predictions_validates(tmp_results: Path, tmp_predictions: Path) -> None:
    """D2(d) — written predictions.json passes the Phase A contract validator."""
    from scripts.refresh_data import refresh_data
    from src.core.predictions_schema import validate_predictions_document

    refresh_data(results_path=tmp_results, predictions_path=tmp_predictions)

    doc = json.loads(tmp_predictions.read_text(encoding="utf-8"))
    errors = validate_predictions_document(doc)
    assert errors == [], f"Contract violations: {errors}"


def test_refresh_data_excel_path_invokes_excel_to_json(tmp_results: Path, tmp_predictions: Path) -> None:
    """D2 — when called without results_path, refresh_data calls excel_to_json."""
    from scripts import refresh_data as rd_module

    # Mock excel_to_json so it doesn't touch any real file; provide a real
    # results_path via generate_predictions_file by patching DATA_PATH too.
    with (
        patch.object(rd_module, "excel_to_json") as mock_excel,
        patch.object(rd_module, "DATA_PATH", tmp_results),
    ):
        rd_module.refresh_data(predictions_path=tmp_predictions)

    mock_excel.assert_called_once()


# ---------------------------------------------------------------------------
# D3 — move_and_convert_file calls refresh_data (not json_converter directly)
# ---------------------------------------------------------------------------

def test_scheduled_run_invokes_refresh(tmp_path: Path) -> None:
    """D3 — move_and_convert_file invokes refresh_data.py, not json_converter.py."""
    import sys
    import subprocess

    scraper_dir = str(
        Path(__file__).resolve().parents[1] / "src" / "scrapers"
    )
    if scraper_dir not in sys.path:
        sys.path.insert(0, scraper_dir)

    import mylotto_scraper

    fake_downloaded = tmp_path / "downloaded.xlsx"
    fake_downloaded.touch()

    captured_cmds: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        m = MagicMock()
        m.returncode = 0
        m.stdout = "ok"
        return m

    with (
        patch("shutil.move"),
        patch("subprocess.run", side_effect=fake_run),
    ):
        scraper = mylotto_scraper.MyLottoScraper.__new__(mylotto_scraper.MyLottoScraper)
        scraper.move_and_convert_file(fake_downloaded)

    assert len(captured_cmds) == 1, "Expected exactly one subprocess call"
    called_script = captured_cmds[0][-1]
    assert "refresh_data" in called_script, (
        f"Expected refresh_data.py to be called, got: {called_script}"
    )


# ---------------------------------------------------------------------------
# D4 — stale / missing / invalid predictions.json always replaced
# ---------------------------------------------------------------------------

def test_regenerates_when_missing(tmp_results: Path, tmp_predictions: Path) -> None:
    """D4 — predictions.json is created even when it doesn't exist before the run."""
    from scripts.refresh_data import refresh_data

    assert not tmp_predictions.exists()
    refresh_data(results_path=tmp_results, predictions_path=tmp_predictions)
    assert tmp_predictions.exists()


def test_regenerates_when_stale(tmp_results: Path, tmp_predictions: Path) -> None:
    """D4 — a stale predictions.json is overwritten with a newer one."""
    from scripts.refresh_data import refresh_data
    from src.core.predictions_schema import validate_predictions_document

    # Write a stale placeholder
    tmp_predictions.write_text('{"stale": true}', encoding="utf-8")
    old_mtime = tmp_predictions.stat().st_mtime

    # Ensure at least 1-ms difference
    time.sleep(0.01)

    refresh_data(results_path=tmp_results, predictions_path=tmp_predictions)

    new_mtime = tmp_predictions.stat().st_mtime
    assert new_mtime > old_mtime, "predictions.json was not overwritten"
    doc = json.loads(tmp_predictions.read_text(encoding="utf-8"))
    assert validate_predictions_document(doc) == []


def test_invalid_existing_is_replaced(tmp_results: Path, tmp_predictions: Path) -> None:
    """D4 — a contract-violating predictions.json is replaced by a valid one."""
    from scripts.refresh_data import refresh_data
    from src.core.predictions_schema import validate_predictions_document

    # Write a file that violates the contract
    bad_doc = {"draw_reference": "not-an-int"}
    tmp_predictions.write_text(json.dumps(bad_doc), encoding="utf-8")

    refresh_data(results_path=tmp_results, predictions_path=tmp_predictions)

    doc = json.loads(tmp_predictions.read_text(encoding="utf-8"))
    assert validate_predictions_document(doc) == []
