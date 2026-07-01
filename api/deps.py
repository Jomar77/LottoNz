"""Data dependency: load results.json once, refresh on mtime change."""

import sys
from pathlib import Path

from api.config import RESEARCH_DIR, RESULTS_JSON

# Add research/ to path so `from src.core.*` imports work (mirrors research/conftest.py).
_research_str = str(RESEARCH_DIR)
if _research_str not in sys.path:
    sys.path.insert(0, _research_str)

from src.core.prediction_engine import load_draws, to_dataframe  # noqa: E402

import pandas as pd


class _DataCache:
    def __init__(self) -> None:
        self._df: pd.DataFrame | None = None
        self._draws: list[dict] | None = None
        self._mtime: float = 0.0

    def _needs_reload(self) -> bool:
        try:
            return RESULTS_JSON.stat().st_mtime != self._mtime
        except FileNotFoundError:
            return True

    def get(self) -> tuple[pd.DataFrame, list[dict]]:
        if self._df is None or self._needs_reload():
            self._draws = load_draws(RESULTS_JSON)
            self._df = to_dataframe(self._draws)
            self._mtime = RESULTS_JSON.stat().st_mtime
        return self._df, self._draws


_cache = _DataCache()


def get_data() -> tuple[pd.DataFrame, list[dict]]:
    """Return (DataFrame, raw draws list), reloading if results.json changed on disk."""
    return _cache.get()
