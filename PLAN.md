# PLAN.md — New 5-Strategy Prediction Algorithm

Implement the prediction framework specified in `new-algo.md` as a feature of the web app.

## Architecture (decided)

- **Backend Python engine** (`backend/src/core/prediction_engine.py`) computes the 5 strategy
  sets and writes a **static** `frontend/public/predictions.json`.
- **Frontend** (`frontend/src/`) fetches `predictions.json` and **displays** labeled strategy
  cards. It does not compute predictions.
- **Mode:** static — predictions regenerate at data-refresh time (whenever `results.json` updates),
  producing a fixed set of predictions for the next draw.
- **Data:** input is `frontend/public/results.json` (1874 draws, 2001-02-17 → 2026-05-09, stored
  most-recent-first, schema `{date, numbers:[6×1–40], powerball:1–10}`). `new-algo.md` shows a CSV
  flow — the real input is this JSON; the loader sorts **ascending** so `.tail(window)` logic works.

## Cross-cutting decisions (apply to every phase)

- **5 strategies, all used:** `burst_volatility`, `mean_reversion`, `momentum_carry`,
  `balanced_hybrid`, `lean_bias`. The default pipeline emits **5** sets (one per strategy).
- **Seeding (required for TDD):** every randomized function takes an injected RNG (`random.Random`
  or `np.random.Generator`); tests assert same-seed reproducibility. `new-algo.md` uses bare
  `random.*` — replace with injected RNG throughout.
- **Injectable time:** never call `datetime.now()` / `pd.Timestamp.today()` in tested paths — inject
  `reference_date` / `generated_at` (default to max draw date / now) so tests are stable.
- **`draw_reference`:** results.json has no official draw number; it is an injectable param
  defaulting to `len(draws)+1` (a sequence index), flagged as such in metadata.
- **No new backend dependencies:** scipy/numpy/pandas are already installed. Frontend adds **Vitest**
  (dev-only) — log it in STATUS.md per CLAUDE.md.
- **TDD is non-negotiable** (CLAUDE.md): failing test first → confirm it fails → minimal implement →
  full suite green → refactor. Commit + check off + update STATUS.md after each item.

---

## Phase A — Shared foundations (do first)

> These tasks gate all parallel work. A single lead agent completes them and commits before Team
> Backend-Engine (Phase B) or Team Frontend (Phase C) start. The frozen contract + fixture are what
> keep the two parallel teams from drifting.

- [x] **A1 — Lock the `predictions.json` schema/contract (single source of truth)**
  - Tests first: Add `backend/tests/test_predictions_contract.py` asserting a canonical example validates against a documented schema — top-level keys (`draw_reference: int`, `generated_at: ISO-8601 UTC string`, `sets: array`, `metadata: object`); each set has `id: int`, `strategy: str` (one of `burst_volatility`, `mean_reversion`, `momentum_carry`, `balanced_hybrid`, `lean_bias`), `main_numbers: 6 ints sorted ascending, each 1–40, unique`, `powerball: int 1–10`, `rationale: non-empty str`; `metadata` has `total_draws_analyzed: int`, `date_range: str`, `uniformity_confirmed: bool`, `chi_square_p_main: float`, `chi_square_p_powerball: float`. Test that an out-of-range powerball, a 5-number main set, and an unsorted main set each fail.
  - Implement: Write the human-readable contract in `backend/docs/predictions_contract.md` (mirroring new-algo.md "Output Format", promoting `main_numbers`/`powerball` as the final key names and enumerating the 5 allowed `strategy` values). Encode it as `validate_predictions_document(doc) -> list[str]` in `backend/src/core/predictions_schema.py`. Add canonical TypeScript types `PredictionsDocument`, `PredictionSet`, `PredictionsMetadata` to `frontend/src/types.ts` (snake_case keys matching the JSON exactly — no remapping). The doc file is the authority; the Python validator and TS types must not diverge from it.
  - Acceptance: `backend/docs/predictions_contract.md` exists; `validate_predictions_document` passes the canonical example and rejects each malformed case; `frontend/src/types.ts` exports the three types; `cd backend && python -m pytest tests/test_predictions_contract.py -v` green; `cd frontend && npx tsc --noEmit` passes.

- [x] **A2 — Commit a shared fixture both teams test against**
  - Tests first: Extend `test_predictions_contract.py` to load `backend/tests/fixtures/predictions.sample.json` from disk and assert `validate_predictions_document` returns no errors (the fixture is the live contract reference, not just an inline literal).
  - Implement: Create `backend/tests/fixtures/predictions.sample.json` — a realistic hand-authored document with all 5 strategy sets, valid sorted main numbers, valid powerballs, plausible metadata. Copy the identical file to `frontend/public/predictions.sample.json` so the frontend slice can render against it before the real engine exists. Note in the contract doc that the two copies must stay byte-identical.
  - Acceptance: Both fixture copies exist and are identical; backend fixture-loading test green; frontend team can fetch/import it to build UI without the engine. Commit before any Phase B/C work begins.

---

## Phase B — Backend prediction engine

> Team Backend-Engine. Touches `backend/` only. Validates its output with the Phase A
> `validate_predictions_document`.

- [x] **B1. Data loader + ascending DataFrame normalization**
  - Tests first: in `backend/tests/test_prediction_engine.py`, `test_load_draws_returns_sorted_ascending` and `test_to_dataframe_schema`. Feed a tiny fixture (results.json shape, most-recent-first); assert `load_draws()`/`to_dataframe()` returns rows sorted **oldest→newest**, a `date` column parsed to `pd.Timestamp`, a list-valued `numbers` column, an int `powerball` column. Assert it reads `frontend/public/results.json` when no path given.
  - Implement: new module `backend/src/core/prediction_engine.py` with `DATA_PATH`/`OUTPUT_PATH` constants (mirroring `decay_generator.py`'s `REPO_ROOT/"frontend"/"public"/...`), `load_draws(path=DATA_PATH) -> list[dict]`, `to_dataframe(draws) -> pd.DataFrame` sorting ascending by date.
  - Acceptance: both tests pass; loader works against the real 1874-row `results.json`.

- [x] **B2. Frequency distributions (overall, quarterly, yearly)**
  - Tests first: `test_calculate_frequencies_overall` (hand-counted fixture → `{1..40: count}`, zero-filled), `test_quarterly_frequencies_shape` (one entry per `(year, quarter)` bucket), `test_yearly_frequencies_shape` (one per year). Fixture spans ≥2 quarters/years.
  - Implement: `calculate_frequencies(draws_or_df) -> dict[int,int]`; `calculate_quarterly_frequencies(df) -> dict[int, list[int]]` via `df.date.dt.to_period("Q")`; `calculate_yearly_frequencies(df) -> dict[int, list[int]]`. All 40 numbers always present (zero-filled) so CV vectors are equal length.
  - Acceptance: counts match hand-computed fixture; all 40 numbers keyed; equal-length vectors per number.

- [x] **B3. Scalar stats — CV and z-score**
  - Tests first: `test_calculate_cv` (known list → std/mean; zero-mean → 0.0), `test_calculate_z_score` (known input → expected; std==0 → 0.0).
  - Implement: `calculate_cv(values) -> float` and `calculate_z_score(current_freq, mean_freq, std_freq) -> float`, both with zero-denominator guards (new-algo.md omits these — we add them).
  - Acceptance: both pass including the guards.

- [x] **B4. Chi-square uniformity test**
  - Tests first: `test_uniformity_true_for_flat` (40 equal freqs → truthy / `p>0.05`), `test_uniformity_false_for_skewed` (one number over-represented → falsy). Assert the p-value helper returns a float in [0,1].
  - Implement: `test_uniformity(frequencies, expected) -> bool` and `uniformity_pvalue(frequencies, expected) -> float` via `scipy.stats.chisquare`.
  - Acceptance: flat passes, skewed fails; p-value helper returns a [0,1] float.

- [x] **B5. Left/right lean classification**
  - Tests first: `test_classify_lean_left` (`[1,2,3,4,30,40]` → "left"), `test_classify_lean_right` (`[1,25,30,33,38,40]` → "right"), tie-rule test (3/3 → "right", per new-algo.md `left if left_count > right_count`).
  - Implement: `LEFT_RANGE=(1,20)`, `RIGHT_RANGE=(21,40)`, `classify_lean(numbers) -> str`.
  - Acceptance: all three pass; tie behavior documented and asserted.

- [x] **B6. Strategy 1 — Burst Volatility set**
  - Tests first: `test_burst_set_size_and_range` (≤6 unique ints in 1–40), `test_burst_prefers_high_cv_recent` (high-CV number present in last 30 draws is selected; high-CV but not recent is excluded).
  - Implement: `generate_burst_set(df, top_n=6) -> list[int]` using quarterly freqs + CV, then `get_recent_numbers(df, last_n_draws=30)` filter. Add helper `get_recent_numbers(df, last_n_draws) -> set[int]`.
  - Acceptance: valid candidate list; recency+CV preference verified.

- [x] **B7. Strategy 2 — Regression (Sleeping Giants) set**
  - Tests first: `test_regression_returns_coldest` (under-represented numbers appear, coldest-first), `test_regression_threshold_relaxes_when_empty` (if no z < −2.0, return the 6 lowest-z numbers rather than <6).
  - Implement: `generate_regression_set(df, z_threshold=-2.0) -> list[int]` with the documented fallback so it always yields up to 6.
  - Acceptance: coldest-first ordering verified; never returns a short list without the fallback.

- [x] **B8. Strategy 3 — Momentum Carry-Over set**
  - Tests first: `test_momentum_returns_hot_in_window` (numbers recurring ≥`min_freq` in last `window` draws → selected, freq-desc), `test_momentum_window_only` (numbers hot only outside the window excluded).
  - Implement: `generate_momentum_set(df, window=30, min_freq=8) -> list[int]` using `df.tail(window)`, with a documented top-up fallback when fewer than 6 clear `min_freq`.
  - Acceptance: window-scoped hot selection verified; freq-descending order.

- [x] **B9. Strategy 4 — Balanced Hybrid set (seeded)**
  - Tests first: `test_hybrid_is_seeded_reproducible` (same seed → identical output), `test_hybrid_composition` (exactly 6 sorted unique ints in 1–40 from hot/cold/neutral buckets).
  - Implement: `generate_hybrid_set(df, rng) -> list[int]` — inject `rng` instead of bare `random.*`; 2 hot + 2 cold + 2 neutral, fill remainder, return `sorted`.
  - Acceptance: deterministic under a fixed seed; always 6 sorted unique valid numbers.

- [x] **B10. Strategy 5 — Left/Right Leaning set**
  - Tests first: `test_lean_set_left_side` (6 numbers all in 1–20 for "left", highest recent freq first), `test_lean_set_right_side` (all in 21–40 for "right"), `test_lean_window_filter` (draws older than `window_years` excluded).
  - Implement: `generate_lean_set(df, lean_direction="left", window_years=1, reference_date=None) -> list[int]`; inject `reference_date` (default = max draw date).
  - Acceptance: correct side + recency ordering; window filter respected; reference date injectable.

- [x] **B11. Powerball selection (hot/cold/cluster/balanced, seeded)**
  - Tests first: `test_pb_hot` (most frequent in recent window), `test_pb_cold` (least frequent overall), `test_pb_cluster` (PB co-occurring most with high-CV mains), `test_pb_balanced_seeded` (weighted-random reproducible under fixed rng). Each result in 1–10.
  - Implement: `select_powerball(df, strategy="balanced", rng=None, window=30) -> int`, plus `get_high_cv_numbers(df)` and `calculate_pb_cooccurrence(df, nums)`. Define "hot" = recent-window most frequent (document this; new-algo.md's `.head(1)` is ambiguous).
  - Acceptance: all four strategies return valid PB; balanced is seed-reproducible.

- [x] **B12. Duplicate avoidance (`avoid_duplicates`)**
  - Tests first: `test_avoid_duplicates_passthrough` (overlap ≤ max_overlap → unchanged), `test_avoid_duplicates_replaces` (overlap > max_overlap → overlapping numbers swapped for non-recent alternatives), `test_avoid_duplicates_preserves_count` (always 6 distinct numbers).
  - Implement: `avoid_duplicates(candidate_nums, recent_numbers, max_overlap=2) -> list[int]`, hardened so it never returns <6 or duplicates.
  - Acceptance: all three pass; output always 6 unique sorted in 1–40.

- [x] **B13. Full pipeline `generate_prediction_sets` (5 sets, seeded, deterministic)**
  - Tests first: `test_generate_sets_count_and_strategies` (default `num_sets=5` → 5 sets tagged `burst_volatility`, `mean_reversion`, `momentum_carry`, `balanced_hybrid`, `lean_bias`, each `{main, pb, strategy}`), `test_pipeline_deterministic` (same seed → identical sets), `test_pipeline_applies_avoid_duplicates` (no set overlaps the last `exclude_recent_draws` draws beyond `max_overlap`).
  - Implement: `generate_prediction_sets(df, num_sets=5, exclude_recent_draws=5, seed=None) -> list[dict]` wiring B6–B12, threading one seeded rng to all randomized steps, using `get_recent_numbers(df, exclude_recent_draws)` for avoidance. Powerball strategy per set: burst→cluster, mean_reversion→cold, momentum→hot, balanced_hybrid→balanced, lean_bias→balanced.
  - Acceptance: returns the 5 strategy-tagged sets; fully reproducible under a seed.

- [x] **B14. Output formatter `format_output` (JSON matching the contract)**
  - Tests first: `test_format_output_schema` (validates against Phase A `validate_predictions_document`), `test_format_output_metadata` (`total_draws_analyzed`, `date_range` = "first to last", `uniformity_confirmed`, `chi_square_p_main`, `chi_square_p_powerball` from B4), `test_generated_at_injectable` (fixed timestamp → verbatim).
  - Implement: `format_output(sets, df, draw_reference=None, generated_at=None) -> dict`; `generated_at` defaults to `datetime.now(UTC)` ISO-Z but injectable; per-strategy `rationale` strings; map internal `main/pb` → output `main_numbers/powerball`; `id` 1-based.
  - Acceptance: emitted dict passes the Phase A validator; deterministic when `generated_at`/`draw_reference` injected.

- [x] **B15. Output validation `validate_output`**
  - Tests first: `test_validate_output_clean` (well-formed → `[]`), `test_validate_output_catches_errors` (wrong main count, out-of-range main, duplicate mains, out-of-range PB, unsorted mains → one error string each).
  - Implement: `validate_output(sets) -> list[str]` per new-algo.md §Testing. Reuse / delegate to Phase A `validate_predictions_document` for the formatted-document check; keep a thin set-level adapter if validating internal `{main, pb}`.
  - Acceptance: empty list for valid input, one descriptive error per violation otherwise.

- [x] **B16. Engine entry point — write `predictions.json`**
  - Tests first: `test_run_writes_predictions_json` (run against a fixture file into a tmp path → file exists, parses, passes `validate_predictions_document`), `test_run_is_deterministic_with_seed` (same seed + injected timestamp → byte-identical file).
  - Implement: public entry `generate_predictions_file(input_path=DATA_PATH, output_path=OUTPUT_PATH, seed=None, generated_at=None, draw_reference=None)` orchestrating load → `to_dataframe` → `generate_prediction_sets` → `format_output` → validate (raise/log if non-empty) → write JSON (`indent=2, ensure_ascii=False`). Add a `__main__`/CLI guard mirroring `decay_generator.py` arg style (`--seed`, `--num-sets`).
  - Acceptance: running the module produces a valid `frontend/public/predictions.json`; full `cd backend && python -m pytest tests/ -v` green.

---

## Phase C — Frontend display

> Team Frontend. Touches `frontend/` only. Builds against `frontend/public/predictions.sample.json`
> from Phase A — does not need the real engine to exist. Additive: must not break the existing
> generator/results UI.

- [x] **C1 — Wire Vitest as the frontend test runner**
  - Tests first: Add `frontend/src/utils.test.ts` with a trivial passing assertion to prove the runner executes. Run `npx vitest run` and confirm discovery.
  - Implement: Add `vitest` to `frontend/package.json` devDependencies; add a `"test": "vitest run"` script; add a minimal `test` block to `frontend/vite.config.ts` (`environment: 'node'`). No production code changes; Vitest must not enter the build.
  - Acceptance: `npx vitest run` exits 0; `npm run build` and `npx tsc --noEmit` still pass. New dep logged in STATUS.md.

- [ ] **C2 — Confirm prediction types resolve (reuse Phase A types)**
  - Tests first: No unit test (type-only). The C3/C4 tests import the types; a compile failure is the signal.
  - Implement: Use the `PredictionsDocument` / `PredictionSet` / `PredictionsMetadata` types created in Phase A (A1) in `frontend/src/types.ts`. Do NOT redefine them. Add only any small frontend-only view-model helpers if needed.
  - Acceptance: `npx tsc --noEmit` passes; C3/C4 import the Phase A types without error.

- [ ] **C3 — Add `fetchPredictions()` to `frontend/src/dataService.ts` (graceful on missing/old file)**
  - Tests first: Add `frontend/src/dataService.test.ts` stubbing global `fetch`: (a) valid body resolves to the parsed `PredictionsDocument`; (b) 404 / `!response.ok` resolves to `null` (no throw); (c) invalid JSON resolves to `null`. Confirm failure first.
  - Implement: `export async function fetchPredictions(): Promise<PredictionsDocument | null>` fetching `/predictions.json`, mirroring `fetchLotteryData` style but returning `null` on non-ok/parse error (`console.error`, no throw). `fetchLotteryData` untouched.
  - Acceptance: all three cases pass under `npx vitest run`; `npx tsc --noEmit` passes.

- [ ] **C4 — Pure display helpers in `frontend/src/utils.ts` (TDD core)**
  - Tests first: Extend `utils.test.ts`: (a) `validatePredictionSet(set)` true only for 6 unique sorted mains in 1–40 and powerball in 1–10 (table-driven failure cases); (b) `formatStrategyLabel('burst_volatility')` → `"Burst Volatility"` with a fallback for unknown strategies; (c) `orderPredictionSets(sets)` orders by `id` ascending and drops malformed sets. Confirm failures first.
  - Implement: add `validatePredictionSet`, `formatStrategyLabel`, `orderPredictionSets` (pure, no DOM) to `frontend/src/utils.ts`.
  - Acceptance: all cases pass under `npx vitest run`; full suite green; `npx tsc --noEmit` passes.

- [ ] **C5 — Render the strategy-cards section**
  - Verify (no unit test — purely presentational JSX; display logic is already unit-tested in C4): manual check in `npm run dev` + `npx tsc --noEmit` + `npm run build`.
  - Implement: Add single-file PascalCase component `frontend/src/PredictedSets.tsx` (Tailwind, lucide-react) taking `PredictionsDocument | null` and rendering one labeled card per set: strategy name via `formatStrategyLabel`, the `rationale`, the 6 `main_numbers` as circular badges, `powerball` as an accent badge — reusing existing badge styling from `App.tsx`. Include a responsible-play disclaimer once at the section footer and optionally surface `metadata` (e.g. `total_draws_analyzed`, `date_range`) as small print. Render nothing (or a subtle "predictions unavailable" note) when the prop is `null`; skip any set failing `validatePredictionSet`. Wire into `App.tsx`: `fetchPredictions()` in a `useEffect` into new state, place `<PredictedSets />` as an additive section without altering the existing layout.
  - Acceptance: cards appear for a sample `predictions.json` in `frontend/public/`; with no file present the existing app still loads/functions; `npx tsc --noEmit` and `npm run build` pass.

- [ ] **C6 — Final gate: type-check, build, full test suite**
  - Verify: run `npx tsc --noEmit`, `npm run build`, `npx vitest run` together; confirm existing results/generator features are visually unaffected in `npm run dev`.
  - Implement: fix any integration issues (imports, config) without touching unrelated files.
  - Acceptance: all three commands exit 0; no regression in existing functionality.

---

## Phase D — Pipeline integration & data contract

> Runs LAST, after Phase B (engine) and Phase C (frontend) are merged. Wires the engine into the
> data-refresh so `frontend/public/predictions.json` regenerates whenever `results.json` does.
> Reuses the contract/validator from Phase A. The only phase that edits files spanning both trees.

- [ ] **D1 — Re-affirm the data contract at the integration boundary**
  - Tests first: `backend/tests/test_predictions_pipeline.py::test_engine_output_matches_contract` — run the real engine on a small fixed results dataset and assert the produced document passes `validate_predictions_document`.
  - Implement: no new logic if B and A agreed; otherwise reconcile the engine writer to the contract (the contract wins). Confirm `generated_at` is UTC ISO-8601 and `draw_reference` derives from the latest draw.
  - Acceptance: engine output validates against the same schema used by the frontend types; test green.

- [ ] **D2 — Single data-refresh orchestrator (converter → engine)**
  - Tests first: `backend/tests/test_refresh_data.py` calls the orchestrator with a temp output dir and asserts: (a) `results.json` written, then (b) `predictions.json` written, (c) `predictions.json` mtime ≥ `results.json` mtime, (d) `predictions.json` validates against the contract. Stub the Excel source via the existing `_find_excel_file` seam / a small fixture workbook so the test is hermetic.
  - Implement: `backend/scripts/refresh_data.py` exposing `refresh_data()` that calls `excel_to_json()` (from `json_converter.py`) then `prediction_engine.generate_predictions_file()`, writing `frontend/public/predictions.json` next to `results.json`. **Use this dedicated orchestrator — NOT a call buried in `json_converter.py`** (keeps the converter single-responsibility and avoids importing scipy/numpy into the lightweight converter; gives one obvious command for humans and the scheduler).
  - Acceptance: `python backend/scripts/refresh_data.py` regenerates both files; engine always runs after the converter; test green.

- [ ] **D3 — Wire the orchestrator into the scheduler/scraper path**
  - Tests first: `test_refresh_data.py::test_scheduled_run_invokes_refresh` — patch `refresh_data` and assert it is called once after a simulated successful scrape.
  - Implement: update the scraper/scheduler completion path (`backend/src/scrapers/scheduler.py`, scheduled by `backend/scripts/run_scheduler.py`) so a successful scrape+download invokes `refresh_data()` instead of calling `excel_to_json()` directly, so predictions regenerate on every 30-day refresh and the startup catch-up run.
  - Acceptance: a successful scheduled/scraper run produces a fresh `predictions.json`; no code path updates `results.json` without also updating `predictions.json`; test green.

- [ ] **D4 — Stale/missing `predictions.json` guard (regenerate on run)**
  - Tests first: `test_refresh_data.py::test_regenerates_when_missing` (delete → run → reappears and validates), `test_regenerates_when_stale` (older than results.json → overwritten and newer), `test_invalid_existing_is_replaced` (contract-violating → replaced by a valid one).
  - Implement: `refresh_data()` unconditionally regenerates predictions.json on each run (no partial/append logic). Frontend absence-handling is owned by Phase C.
  - Acceptance: missing, stale, or invalid predictions.json is always replaced by a valid, contract-conforming file after a refresh; tests green.

- [ ] **D5 — Docs, run instructions, committed-artifact treatment**
  - Tests first: N/A (docs/config). Manual check: `git check-ignore -v frontend/public/predictions.json` returns no match (committable), mirroring `results.json`.
  - Implement: In `CLAUDE.md`, update the **data-flow** line (scraper → `json_converter.py` writes `results.json` → `prediction_engine.py` writes `predictions.json` → React fetches both) and add a **How to run** entry: `cd backend && python scripts/refresh_data.py`. Ensure `.gitignore` treats `predictions.json` identically to `results.json`. **Commit `predictions.json` like `results.json`** — it is a static artifact the Vercel frontend fetches at runtime; committing keeps deploys reproducible without running the backend in CI.
  - Acceptance: `CLAUDE.md` reflects the engine step and `refresh_data.py`; `.gitignore` treats predictions.json like results.json; `predictions.json` is tracked by git after a refresh.

---

## Execution plan — agent teams

> Guidance for orchestrating subagent teams during execution. Not a checklist — it describes how to
> parallelize the phases above.

### Phases and ownership
- **Phase A — Shared foundations** → one **Lead** agent. Locks the contract
  (`backend/docs/predictions_contract.md`, `backend/src/core/predictions_schema.py`,
  `frontend/src/types.ts`) and the shared fixture (`backend/tests/fixtures/predictions.sample.json`
  + frontend copy). Must finish and commit before anything else starts.
- **Phase B — Prediction engine** → **Team Backend-Engine**. Owns `backend/` only. Implements the 5
  strategies + JSON writer; validates output with the Phase A validator.
- **Phase C — Frontend display** → **Team Frontend**. Owns `frontend/src/` only. Builds against the
  Phase A sample fixture; does not need the real engine.
- **Phase D — Pipeline integration** → **Lead / dedicated Integration agent**, LAST. Wires engine
  into the data-refresh; updates docs/gitignore. Touches seams across both trees.

### Dependency graph
```
        A  (lead, sequential, must commit first)
       / \
      B   C        ← Team Backend-Engine and Team Frontend run CONCURRENTLY
       \ /
        D  (lead, sequential, after B and C merged)
```
- Sequential: A → {B, C} → D.
- Concurrent: B and C run fully in parallel. They share no source files — only the immutable Phase A
  contract + fixture. Neither blocks the other.

### Shared contract = coordination point
`backend/docs/predictions_contract.md` is the single coordination artifact. Both teams code to it;
neither may change it unilaterally. If a team discovers the contract is wrong, that is a
**circuit-breaker** (needs lead/human decision) — stop, document in STATUS.md, do not silently
diverge. The Phase A schema validator (Python) and TS types are the enforcement that catches drift at
test/compile time on both sides.

### Disjoint directories → true parallelism, no merge conflicts
Team Backend-Engine touches only `backend/`; Team Frontend touches only `frontend/src/`. These sets
are disjoint → simultaneous work with zero merge conflicts. The only files both depend on (the
contract doc, the two fixture copies, `frontend/src/types.ts`) are written once in Phase A and treated
as read-only thereafter. Phase D is the only phase editing files spanning both trees, which is why it
runs alone, last.

### TDD + circuit breakers + bookkeeping under parallel agents
- **TDD per item (non-negotiable):** each team writes the failing test first, confirms it fails for
  the right reason, implements minimally, runs its **own full suite**
  (`cd backend && python -m pytest tests/ -v` for B/D; `npx vitest run` + `npx tsc --noEmit` +
  `npm run build` for C), then refactors green — before checking the item off.
- **Commit granularity:** every agent commits after each completed item (conventional commits), never
  batching. Disjoint directories mean parallel B/C commits don't collide.
- **PLAN.md / STATUS.md bookkeeping:** each team checks off only its own `[ ]` items and appends a
  clearly namespaced section to `STATUS.md` (e.g. `### [Team Backend-Engine]`, `### [Team Frontend]`)
  rather than editing shared lines; the lead reconciles before Phase D.
- **Circuit breakers (CLAUDE.md):** apply per-agent — a test failing >3× on the same fix, a command
  erroring >2× consecutively, a needed human decision, or a new dependency → stop that item, document
  in STATUS.md, commit partial progress, move on. A contract ambiguity is the most likely breaker;
  route it to the lead, never fork the contract.
- **Session handoff:** each agent updates `SESSION_NOTES.md` before stopping (completed work,
  decisions, remaining unchecked items, anything needing human review) so the lead integrates in
  Phase D with full context.
