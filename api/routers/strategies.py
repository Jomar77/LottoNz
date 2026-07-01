"""GET /predict/strategies router."""

from fastapi import APIRouter, Query

from api.schemas import LeanType, SpreadType, StrategiesResponse
from api.services.strategies_service import generate_strategies

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get(
    "/strategies",
    response_model=StrategiesResponse,
    summary="Generate 5-strategy prediction sets",
    description="""
Run the full five-strategy prediction engine against historical draw data and return
up to five algorithmically distinct number sets.

| Strategy | Logic |
|---|---|
| `burst_volatility` | High-CV numbers that appear in tight clusters |
| `mean_reversion` | Numbers most below their long-run expected frequency |
| `momentum_carry` | Most frequent numbers in the recent 30-draw window |
| `balanced_hybrid` | 2 hot + 2 cold + 2 neutral numbers (seeded) |
| `lean_bias` | Highest-frequency numbers from the dominant range side |

**`lean`** overrides the direction used by the `lean_bias` strategy.
**`date_from`** slices the historical dataset — requires ≥ 100 draws in the window.
**`spread`** and **`consecutive`** are stored in `applied_filters` but do not constrain
strategy outputs (strategies are data-driven, not constraint-driven).

Omit `seed` for a fresh result each call (output will differ from the static
`predictions.json`).
""",
)
def predict_strategies(
    lean: LeanType = Query(LeanType.middle, description="Overrides the `lean_bias` strategy direction: `left` (1–20), `right` (21–40), `middle` = auto-detect from data"),
    spread: SpreadType = Query(SpreadType.mixed, description="Advisory preference stored in `applied_filters` — does not filter strategy outputs"),
    consecutive: bool = Query(False, description="Advisory preference stored in `applied_filters` — does not filter strategy outputs"),
    date_from: str | None = Query(
        None,
        description="Analyze only draws on/after this date (`YYYY-MM-DD`). Minimum 100 draws must remain after filtering.",
        examples=["2023-01-01"],
    ),
    count: int = Query(5, ge=1, le=5, description="Number of strategy sets to return (1–5)"),
    seed: int | None = Query(None, description="Integer RNG seed for the `balanced_hybrid` and `lean_bias` powerball steps — omit for fresh output"),
) -> StrategiesResponse:
    return generate_strategies(
        lean=lean,
        spread=spread,
        consecutive=consecutive,
        date_from=date_from,
        count=count,
        seed=seed,
    )
