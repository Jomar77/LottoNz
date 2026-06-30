# CLAUDE.md

<!-- ============================================================ -->
<!-- FILL IN THE THREE SECTIONS BELOW BEFORE YOUR FIRST RUN.      -->
<!-- Everything under the line is ready to use as-is.            -->
<!-- ============================================================ -->

## Stack

- **Research**: Python 3.14, pandas, scipy, numpy — `research/` (engines, scrapers, notebooks)
- **API**: FastAPI + uvicorn — `api/` (parametric endpoints, wraps research engines)
- **Frontend**: React 18, TypeScript (strict), Vite, Tailwind CSS — `Frontend/`
- **Test runners**: pytest (research + api), Vitest (frontend)
- **Static data**: `Frontend/public/results.json` (1874 draws), `Frontend/public/predictions.json` (engine output)

## Conventions

- Components: PascalCase (`PatternExplorer.tsx`), colocated in `frontend/src/`
- Python: snake_case functions, type hints, injectable time/RNG for testability
- Commits: conventional commits (`feat:`, `fix:`, `refine:`, `chore:`)
- Tests: TDD — failing test first, then implementation (see Testing strategy below)

## How to run

```
# Research/engine tests
cd research && python -m pytest tests/ -q

# API tests
cd <repo-root> && python -m pytest api/tests/ -q

# API dev server (http://localhost:8000)
cd <repo-root> && uvicorn api.main:app --reload

# Frontend tests + type check + build
cd Frontend && npm run test && npx tsc --noEmit && npm run build

# Frontend dev server (http://localhost:5173)
cd Frontend && npm run dev

# Refresh data (Excel → results.json → predictions.json)
cd research && python scripts/refresh_data.py

# Regenerate predictions only (skip Excel step)
cd research && python scripts/refresh_data.py --predictions-only
```

## Data flow

```
mylotto.co.nz
   └─ research/src/scrapers/mylotto_scraper.py  (downloads december.xlsx)
      └─ research/scripts/refresh_data.py  (orchestrator — called by scraper before git commit)
         ├─ research/src/utils/json_converter.py  → Frontend/public/results.json
         └─ research/src/core/prediction_engine.py → Frontend/public/predictions.json
                                                       ↓
                                             React fetches both at runtime (static, default view)

api/                              ← parametric "generate your own" feature
   GET /predict/weighted          ← frequency-weighted tickets with lean/spread/consecutive
   GET /predict/strategies        ← 5-strategy engine with date_from filtering
```

Both `results.json` and `predictions.json` are committed artifacts (not gitignored).
They update together on every 30-day scraper run.

<!-- ============================================================ -->
<!-- READY TO USE — no edits needed below this line.             -->
<!-- ============================================================ -->

---

## Testing strategy — TDD (non-negotiable)

This project uses test-driven development. For every PLAN.md item:

1. **Write the test first.** Write failing tests that encode the acceptance criteria before writing any implementation.
2. **Run the test, confirm it fails** for the right reason.
3. **Implement** the minimum code to make the test pass.
4. **Run the full test suite** — not just the new test.
5. **Refactor** if needed, keeping tests green.
6. Only mark the item done when the full suite passes.

Never write implementation before its test. Never commit code with failing tests.

---

## Autonomous execution rules (/yolo)

When running /yolo, work through PLAN.md:

1. Read PLAN.md at the start of every session.
2. Work through unchecked items `[ ]` sequentially — do not skip or reorder.
3. For each item, apply the TDD cycle above.
4. After completing each item:
   - Run the full test suite
   - Commit with a descriptive conventional-commit message
   - Check off the item `[x]` in PLAN.md
   - Append progress to STATUS.md (what was done, decisions made)
5. Before stopping for any reason, write/update SESSION_NOTES.md with:
   - What was completed this session
   - Design decisions made and why
   - What remains unchecked in PLAN.md
   - Anything the human must review or approve

## Circuit breakers

If any of these occur: stop the current item, document it in STATUS.md, commit partial progress, and move to the next PLAN.md item.

- A test fails more than 3 times on the same fix attempt
- A command errors more than 2 times consecutively
- A task needs a human decision (architecture, external API choice, etc.)
- A task requires a new dependency not already in the project

Never keep retrying the same failing approach. Document and move on.

## Definition of done

An item is checked off `[x]` only when:
- It meets the acceptance criteria written in PLAN.md
- New behaviour has tests, written test-first
- The full test suite passes
- The work is committed

---

## Security rules (non-negotiable)

- NEVER read, print, log, or reference .env files or files containing secrets
- NEVER run commands outside this project directory
- NEVER use `git push --force`
- NEVER run `rm -rf` on any directory
- NEVER print environment variable values — reference by name only
- If a task needs a secret that isn't available, document in STATUS.md and skip it
- Use .env.example for any secret references in committed code
- NEVER commit node_modules, build/, or dist/

## Git behaviour

- Work on the current branch unless PLAN.md says otherwise
- Commit after each completed item — do not batch multiple items into one commit
- Commit messages describe what changed and why
- Do not push unless PLAN.md explicitly says to push and open a PR

## What not to touch

- Do not modify .env files or .claudeignore
- Do not modify this CLAUDE.md unless a PLAN.md item explicitly requires it
- Do not install new dependencies without noting it in STATUS.md first
- Do not refactor files unrelated to the current PLAN.md item

## Token efficiency

- Prefer reading specific files over whole directories
- Use search/grep to locate code before reading full files
- Do not re-read unchanged files
- Keep this file under 200 lines — it loads on every turn
