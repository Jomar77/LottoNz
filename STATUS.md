# STATUS.md

## Phase A — Shared foundations (Lead)

### [Lead] A1 — Contract locked
- Added `backend/tests/test_predictions_contract.py` (TDD, 28 cases) — written and
  confirmed red before implementation.
- Implemented `backend/src/core/predictions_schema.py` →
  `validate_predictions_document(doc) -> list[str]`.
- Wrote the human-readable authority `backend/docs/predictions_contract.md`.
- Added TS types `PredictionStrategy`, `PredictionSet`, `PredictionsMetadata`,
  `PredictionsDocument` to `frontend/src/types.ts` (snake_case, no remapping).

### [Lead] A2 — Shared fixture
- `backend/tests/fixtures/predictions.sample.json` (all 5 strategy sets, valid).
- Copied byte-identical to `frontend/public/predictions.sample.json`
  (enforced by `test_frontend_fixture_is_byte_identical`).

### Decisions / notes
- **Foundation fix (out of original plan scope, required):** `backend/src/core/__init__.py`
  did `from .lotto_generator import *`, and `lotto_generator.py` reads
  `lotto-data/december.xlsx` at **import time**. This made `import src.core.<anything>`
  crash, which would have blocked every Phase B import too. Changed `__init__.py` to not
  eagerly import side-effectful modules (`lotto_generator` is run standalone as a script).
  Verified the existing `test_lotto_generator.py` / `test_scraper.py` still pass.
- Added `backend/conftest.py` so `src.*` imports resolve from the backend root
  (no pytest config existed previously; old test used ad-hoc `sys.path` insertion).
- `generated_at` validation requires a timezone-aware UTC ISO-8601 string (accepts
  trailing `Z`).
- Responsible-play framing baked into the contract doc and the fixture rationales
  (each set explicitly states past patterns do not predict draws). Pending review of
  UX / devil's-advocate teammate findings before Phase C framing is finalized.

### Verification
- `cd backend && python -m pytest tests/ -v` → 30 passed.
- `cd frontend && npx tsc --noEmit` → exit 0.

### Remaining
- Phase B (engine, B1–B16) and Phase C (frontend, C1–C6) — run concurrently.
- Phase D (integration, D1–D5) — last.
