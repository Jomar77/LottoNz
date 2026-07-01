"""API configuration — all paths and tunables in one place."""

import os
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
REPO_ROOT = API_DIR.parent
RESEARCH_DIR = REPO_ROOT / "research"

RESULTS_JSON = Path(
    os.environ.get("RESULTS_JSON_PATH", str(REPO_ROOT / "Frontend" / "public" / "results.json"))
)

CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

MIN_DRAWS_FOR_DATE_FILTER = 100
MAX_WEIGHTED_COUNT = 20
MAX_STRATEGIES_COUNT = 5
MAX_REJECTION_ATTEMPTS = 200
