"""GET /predict/strategies/weighted router."""

from fastapi import APIRouter, Query

from api.schemas import LeanType, SpreadType, StrategiesWeightedResponse
from api.services.strategies_weighted_service import generate_strategies_weighted

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get(
    "/strategies/weighted",
    response_model=StrategiesWeightedResponse,
    summary="Generate 5-strategy sets with enforced lean/spread/consecutive constraints",
    description="""
Run the full five-strategy prediction engine and **enforce** lean, spread, and
consecutive constraints on every set via a deterministic minimal-swap repair
(lean → spread → consecutive, budget = 3 substitutions per set).

Unlike `/predict/strategies` where `lean`, `spread`, and `consecutive` are advisory
only, this endpoint guarantees that each returned set either satisfies all three
constraints *or* reports `constraint_satisfied: false` (best-effort, mirrors
`/predict/weighted` behaviour).

| Strategy | Logic |
|---|---|
| `burst_volatility` | High-CV numbers that appear in tight clusters |
| `mean_reversion` | Numbers most below their long-run expected frequency |
| `momentum_carry` | Most frequent numbers in the recent 30-draw window |
| `balanced_hybrid` | 2 hot + 2 cold + 2 neutral numbers (seeded) |
| `lean_bias` | Highest-frequency numbers from the dominant range side |

`metadata.applied_filters.enforcement` is always `"active"` to distinguish this
endpoint from the advisory `/predict/strategies` response.
""",
)
def predict_strategies_weighted(
    lean: LeanType = Query(LeanType.middle, description="`left` = enforce ≥4 numbers ≤20, `right` = enforce ≥4 numbers >20, `middle` = no lean constraint"),
    spread: SpreadType = Query(SpreadType.mixed, description="`tight` = enforce max−min ≤ 20, `wide` = enforce max−min ≥ 20, `mixed` = no spread constraint"),
    consecutive: bool = Query(False, description="If `true`, enforce at least one consecutive pair per set; if `false`, enforce no consecutive pairs"),
    date_from: str | None = Query(
        None,
        description="Analyze only draws on/after this date (`YYYY-MM-DD`). Minimum 100 draws must remain.",
        examples=["2023-01-01"],
    ),
    count: int = Query(5, ge=1, le=5, description="Number of strategy sets to return (1–5)"),
    seed: int | None = Query(None, description="Integer RNG seed for the `balanced_hybrid` and `lean_bias` powerball steps"),
) -> StrategiesWeightedResponse:
    return generate_strategies_weighted(
        lean=lean,
        spread=spread,
        consecutive=consecutive,
        date_from=date_from,
        count=count,
        seed=seed,
    )
