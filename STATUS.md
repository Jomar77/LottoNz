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

---

## Phase C — Frontend display (Lead)

All C1–C6 complete. Frontend Vitest suite: 18 tests pass. `tsc --noEmit`, `npm run build` all green.

### Items completed
- C1: Vitest wired, bootstrap test green
- C2: Phase A TS types reused without redefinition
- C3: `fetchPredictions()` added to `dataService.ts`, 3 tests
- C4: `validatePredictionSet`, `formatStrategyLabel`, `formatFallacyLabel`, `formatFallacyExplanation`, `orderPredictionSets` in `utils.ts`, 15 tests
- C5: `PatternExplorer.tsx` — educational framing, 5 fallacy-labeled strategy cards (named Gambler's Fallacy, Hot-Hand Fallacy, Clustering Fallacy, Diversification Fallacy, Positional Bias Fallacy), uniformity hero stat, NZ gambling helpline footer. Wired into `App.tsx` via `useEffect` + state below the existing two-column layout.
- C6: All three gate commands pass

### Key decisions
- Component named `PatternExplorer` (not `PredictedSets`) — "Pattern Explorer" is the section title; avoids predictive language
- Educational framing: fallacy badge per card, explanation text that ends in "each draw is independent", no bounce animation
- Hero stat: chi_square_p_main + total_draws_analyzed — the science result is foregrounded
- `chi_square_p_powerball = 4e-05` (non-uniform): UniformityHero shows the conditional branch for non-uniform powerball without alarming language
- Insertion point: full-width below both sticky columns, above mobile picker modal (line 493 in App.tsx)
- No mock/stub for C5 — presentational only, verified via type-check + build

---

## Phase D — Pipeline integration (Lead)

All D1–D5 complete. 88 backend tests pass (77 original + 3 D1 pipeline + 8 D2/D3/D4).

### Items completed
- D1: `test_predictions_pipeline.py` — engine output validated against Phase A contract on a 10-row fixture
- D2: `backend/scripts/refresh_data.py` with injectable `results_path`/`predictions_path` seams; `test_refresh_data.py` (8 tests) covering write, mtime ordering, contract validation, and mock-excel path
- D3: `mylotto_scraper.py` `move_and_convert_file` now calls `REFRESH_SCRIPT` (refresh_data.py) instead of `CONVERT_SCRIPT` (json_converter.py) — both results.json and predictions.json are updated before git_commit_and_push runs
- D4: refresh_data() always regenerates unconditionally — missing, stale, and invalid predictions.json all replaced correctly
- D5: CLAUDE.md updated with Stack, Conventions, How to run, and data-flow diagram. Both results.json and predictions.json are not gitignored (confirmed with git check-ignore).

### Key decisions
- **D3 ordering fix**: scraper subprocess changed from `json_converter.py` → `refresh_data.py`; predictions.json now generated inside `move_and_convert_file()`, before `git_commit_and_push()` — both files land in the same commit
- **`src/utils/__init__.py`** had same import-time side-effect bug as `core/__init__.py` (`data_cleaner.py` calls its own function at module level). Fixed by replacing star-imports with `__all__ = []`
- **Test isolation**: `test_refresh_data_excel_path_invokes_excel_to_json` patches both `excel_to_json` AND `DATA_PATH` to avoid clobbering the real results.json

### Phase D — BLOCKED on one human decision (RESOLVED)
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
