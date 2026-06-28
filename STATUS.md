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

---

## Phase B — Backend prediction engine (Lead)

All B1–B16 complete. 77 backend tests pass. Engine runs against real 1874-row
results.json and produces a valid predictions.json.

### Key decisions made
- **RNG type locked to `random.Random`** — consistent with new-algo.md API
  (`random.sample`, `random.choice`, `random.choices`). One instance seeded once
  in B13, consumed in fixed call order through hybrid set + both balanced PBs.
- **B6 top-up**: `generate_burst_set` now always returns exactly 6 sorted numbers
  (added `_pad_to_n` helper; the original "≤6" was wrong per contract).
- **B12 both branches sort**: `avoid_duplicates` passthrough and replacement both
  return `sorted(result)`. Pool-dry case handled by a fallback list.
- **B11 "hot" = recent-window** (not overall), clarifying new-algo.md ambiguity.
- **Rationale copy**: descriptive, no predictive language. "mean_reversion" avoids
  "due for regression" (UX teammate flagged this encodes the gambler's fallacy).
- **uniformity_confirmed** based on chi-square p-value of MAIN numbers.

### chi_square_p_powerball on real data
On the 1874-row real dataset the powerball chi-square p-value is `4e-05` — the
powerball distribution is NOT uniform. This is a real data finding, not a bug.
`uniformity_confirmed` covers only the main numbers (as documented). The metadata
field surfaces the raw PB p-value so the UI can decide how to present this.

### Phase C — PAUSED (user decision)
User chose to finish Phase B first and decide on framing (educational vs
entertainment) before building the UI (Phase C). See teammate findings in
SESSION_NOTES.md.

### Phase D — BLOCKED on one human decision
The exec-explorer identified an ordering bug in D3:
- Inside `mylotto_scraper.py`, `move_and_convert_file()` runs at line 408, then
  `git_commit_and_push()` at line 415-421 — both INSIDE `scrape()`.
- If D3 wires `refresh_data()` into the SCHEDULER after `scrape()` returns,
  `predictions.json` is generated AFTER the git auto-commit → never committed.
- To be in the same commit as `results.json`, the engine must run inside `scrape()`
  BEFORE the git step (inside `move_and_convert_file` or after it but before the
  commit), which contradicts D2's "dedicated orchestrator, NOT buried in the
  converter" preference.
- **Needs a human/lead decision** before D3 can be implemented.
