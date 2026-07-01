"""GET /predict/weighted router."""

from fastapi import APIRouter, Query

from api.schemas import LeanType, SpreadType, WeightedResponse
from api.services.weighted_service import generate_weighted

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get(
    "/weighted",
    response_model=WeightedResponse,
    summary="Generate frequency-weighted tickets",
    description="""
Generate one or more tickets using a **radioactive-decay-inspired** sampling model.

- **classic** mode weights each ball by its Laplace-smoothed historical frequency.
- **temporal** mode applies exponential decay so recent appearances matter more.

Constraints (`lean`, `spread`, `consecutive`) are enforced via rejection sampling
(up to 200 attempts per ticket). If a combination is unsatisfiable in 200 tries
the closest result is returned and `constraint_satisfied` is `false`.

Omit `seed` for a fresh random result each call. Pass the same `seed` to reproduce
an earlier result exactly.
""",
)
def predict_weighted(
    count: int = Query(1, ge=1, le=20, description="Number of tickets to generate (1–20)"),
    lean: LeanType = Query(LeanType.middle, description="`left` = favour 1–20, `right` = favour 21–40, `middle` = no bias"),
    spread: SpreadType = Query(SpreadType.mixed, description="`tight` = max−min ≤ 20, `wide` = max−min ≥ 20, `mixed` = no constraint"),
    consecutive: bool = Query(False, description="If `true`, every ticket will contain at least one consecutive pair"),
    mode: str = Query("classic", pattern="^(classic|temporal)$", description="`classic` = flat historical weight, `temporal` = recency-biased exponential decay"),
    seed: int | None = Query(None, description="Integer RNG seed — omit for non-deterministic output"),
) -> WeightedResponse:
    return generate_weighted(
        count=count,
        lean=lean,
        spread=spread,
        consecutive=consecutive,
        mode=mode,
        seed=seed,
    )
