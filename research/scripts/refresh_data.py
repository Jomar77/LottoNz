"""Data-refresh orchestrator.

Runs the Excel → results.json conversion, then the prediction engine that
writes predictions.json. Both files are updated before any git commit so
they land in the same commit.

Usage
-----
    python backend/scripts/refresh_data.py          # full refresh (Excel → JSON → predictions)
    python backend/scripts/refresh_data.py --predictions-only  # skip Excel step (for testing)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure backend root is on sys.path when run as a script
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from src.utils.json_converter import excel_to_json  # noqa: E402
from src.core.prediction_engine import (  # noqa: E402
    generate_predictions_file,
    DATA_PATH,
    OUTPUT_PATH,
)


def refresh_data(
    results_path: Path | None = None,
    predictions_path: Path | None = None,
) -> None:
    """Run the full data refresh.

    Parameters
    ----------
    results_path:
        Path to an existing results.json. When supplied, the Excel conversion
        step is skipped (useful for tests or when results.json is already fresh).
    predictions_path:
        Destination for predictions.json. Defaults to OUTPUT_PATH.
    """
    if results_path is None:
        # Production path: convert Excel → results.json first
        excel_to_json()
        results_path = DATA_PATH

    generate_predictions_file(
        input_path=results_path,
        output_path=predictions_path or OUTPUT_PATH,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh results.json and predictions.json")
    parser.add_argument(
        "--predictions-only",
        action="store_true",
        help="Skip Excel conversion; regenerate predictions.json from existing results.json",
    )
    args = parser.parse_args()

    if args.predictions_only:
        refresh_data(results_path=DATA_PATH)
    else:
        refresh_data()


if __name__ == "__main__":
    main()
