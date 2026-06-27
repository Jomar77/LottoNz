"""5-strategy NZ Lotto prediction engine (Phase B).

Reads historical draws from ``frontend/public/results.json`` and produces a
static ``frontend/public/predictions.json`` containing five strategically
distinct number sets. See ``backend/docs/predictions_contract.md`` for the
output contract and ``new-algo.md`` for the analytical framework.

> NZ Lotto draws are independent, uniform-random events. The "strategies" here
> surface historical patterns for entertainment/education only — they carry no
> predictive edge over a random pick.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (mirror decay_generator.py)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DATA_PATH = REPO_ROOT / "frontend" / "public" / "results.json"
OUTPUT_PATH = REPO_ROOT / "frontend" / "public" / "predictions.json"

MAIN_MIN, MAIN_MAX = 1, 40
POWERBALL_MIN, POWERBALL_MAX = 1, 10
NUMBERS_PER_DRAW = 6


# ---------------------------------------------------------------------------
# B1 — Data loading + ascending DataFrame normalization
# ---------------------------------------------------------------------------
def load_draws(path: Path | str = DATA_PATH) -> list[dict]:
    """Load raw draw dicts from a results.json file (most-recent-first on disk)."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def to_dataframe(draws: list[dict]) -> pd.DataFrame:
    """Normalize raw draws into a DataFrame sorted oldest -> newest.

    Columns:
      - ``date``: ``pd.Timestamp``
      - ``numbers``: list[int] of the 6 main numbers
      - ``powerball``: int
    """
    df = pd.DataFrame(draws)
    df["date"] = pd.to_datetime(df["date"])
    df["numbers"] = df["numbers"].apply(lambda nums: [int(n) for n in nums])
    df["powerball"] = df["powerball"].astype(int)
    df = df.sort_values("date").reset_index(drop=True)
    return df
