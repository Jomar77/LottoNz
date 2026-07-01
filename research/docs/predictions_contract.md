# predictions.json — Data Contract (single source of truth)

This document is the **authority** for the shape of `frontend/public/predictions.json`.
Both the backend engine (Phase B, `prediction_engine.py`) and the frontend display
(Phase C, `frontend/src/`) code against it.

Enforcement on both sides must not diverge from this file:

- **Backend:** `backend/src/core/predictions_schema.py` →
  `validate_predictions_document(doc) -> list[str]` (empty list == valid).
- **Frontend:** `frontend/src/types.ts` → `PredictionsDocument`, `PredictionSet`,
  `PredictionsMetadata` (snake_case keys matching the JSON exactly — no remapping).

If a team finds this contract is wrong, that is a **circuit-breaker**: stop, document
in `STATUS.md`, and escalate to the lead. Do not silently fork the contract.

> ⚠️ **Responsible-play note.** These sets are themed alternatives to a random pick.
> NZ Lotto draws are independent, uniform-random events; none of the strategies has any
> predictive edge. The document is for entertainment/education only.

---

## Top-level object

| Key | Type | Rules |
|-----|------|-------|
| `draw_reference` | `int` | Sequence index for the draw the sets target. results.json has no official draw number, so this defaults to `len(draws) + 1` and is flagged as a sequence index in code, not an official draw id. |
| `generated_at` | `string` | ISO-8601 **UTC** timestamp (e.g. `2026-05-09T08:00:00Z`). Must be timezone-aware and represent UTC. |
| `sets` | `array` | Non-empty array of [Prediction Set](#prediction-set) objects. The default pipeline emits exactly **5**, one per strategy. |
| `metadata` | `object` | [Metadata](#metadata) object. |

## Prediction Set

| Key | Type | Rules |
|-----|------|-------|
| `id` | `int` | 1-based set identifier. |
| `strategy` | `string` | One of: `burst_volatility`, `mean_reversion`, `momentum_carry`, `balanced_hybrid`, `lean_bias`. |
| `main_numbers` | `int[]` | Exactly **6** integers, each within **1–40**, **unique**, **sorted ascending**. |
| `powerball` | `int` | Within **1–10**. |
| `rationale` | `string` | Non-empty, human-readable explanation of the set. |

These are the final output key names: internally the engine uses `main`/`pb`, but the
formatter maps them to `main_numbers`/`powerball` for this document.

## Metadata

| Key | Type | Rules |
|-----|------|-------|
| `total_draws_analyzed` | `int` | Number of draws used. |
| `date_range` | `string` | Non-empty, `"<first> to <last>"` (e.g. `2001-02-17 to 2026-05-09`). |
| `uniformity_confirmed` | `bool` | Whether the chi-square uniformity test passed (`p > 0.05`). |
| `chi_square_p_main` | `float` | p-value for main numbers, within `0.0`–`1.0`. |
| `chi_square_p_powerball` | `float` | p-value for the powerball, within `0.0`–`1.0`. |

---

## Canonical example

See `backend/tests/fixtures/predictions.sample.json`. **This fixture is copied
byte-identically to `frontend/public/predictions.sample.json`** so the frontend can
render against it before the real engine exists. The two copies **must stay
byte-identical** (enforced by `test_frontend_fixture_is_byte_identical`). When you
change one, regenerate the other and re-run the contract tests.

```json
{
  "draw_reference": 1875,
  "generated_at": "2026-05-09T08:00:00Z",
  "sets": [
    {
      "id": 1,
      "strategy": "burst_volatility",
      "main_numbers": [2, 5, 7, 11, 28, 35],
      "powerball": 3,
      "rationale": "High-CV numbers with recent clustering behaviour."
    }
  ],
  "metadata": {
    "total_draws_analyzed": 1874,
    "date_range": "2001-02-17 to 2026-05-09",
    "uniformity_confirmed": true,
    "chi_square_p_main": 0.585,
    "chi_square_p_powerball": 0.178
  }
}
```
