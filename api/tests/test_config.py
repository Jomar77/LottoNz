"""Config path constants resolve against the real (post-rename) repo layout."""

from api.config import REPO_ROOT, RESEARCH_DIR, RESULTS_JSON


def test_research_dir_points_at_real_research_folder():
    assert RESEARCH_DIR == REPO_ROOT / "research"
    assert RESEARCH_DIR.is_dir()
    assert (RESEARCH_DIR / "src" / "core" / "prediction_engine.py").is_file()


def test_results_json_default_resolves_to_real_file():
    assert RESULTS_JSON == REPO_ROOT / "frontend" / "public" / "results.json"
    assert RESULTS_JSON.is_file()
