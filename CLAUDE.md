# CLAUDE.md

## Stack

**Frontend** (`frontend/`)
- Runtime: Node.js 24, TypeScript 5 (strict)
- Framework: React 18 + Vite 5
- Styling: Tailwind CSS 3
- Icons: lucide-react
- Package manager: npm
- Deploy: Vercel (`frontend/vercel.json`)

**Backend** (`backend/`)
- Runtime: Python 3.14
- Scraping: Selenium + Firefox (GeckoDriver via webdriver-manager), BeautifulSoup4
- Data: pandas, numpy, scipy, openpyxl
- Config: python-dotenv
- Tests: pytest + pytest-cov

**Data flow:** Python scraper downloads Excel from mylotto.co.nz → `json_converter.py` converts to `frontend/public/results.json` → React app fetches `/results.json` at runtime.

## Conventions

**Frontend**
- Components: PascalCase (`App.tsx`); single-file components — no separate style files
- Functions/vars: camelCase
- Types in `src/types.ts`; utilities in `src/utils.ts`; data fetching in `src/dataService.ts`
- No test framework currently wired for frontend (Vite only, no Vitest/Jest config)

**Backend**
- Modules: `snake_case` files under `backend/src/{core,scrapers,utils}/`
- Tests: `backend/tests/test_*.py` with pytest
- Scheduler runs scraper every 30 days; tracks last run in `backend/src/scrapers/last_run.json`

**Commits:** conventional commits (`feat:`, `fix:`, `chore:`, `refactor:`)

**NZ Lotto rules:** 6 main numbers drawn from 1–40, 1 Powerball from 1–10.

## How to run

**Frontend dev server:**
```bash
cd frontend && npm run dev
# → http://localhost:5173/
```

**Frontend type check:**
```bash
cd frontend && npx tsc --noEmit
```

**Frontend build:**
```bash
cd frontend && npm run build
```

**Backend tests:**
```bash
cd backend && python -m pytest tests/ -v
```

**Backend — convert Excel to JSON:**
```bash
cd backend && python src/utils/json_converter.py
# Outputs to frontend/public/results.json
```

**Backend — run scraper manually:**
```bash
cd backend && python src/scrapers/mylotto_scraper.py
```

**Backend — run scheduler:**
```bash
cd backend && python scripts/run_scheduler.py
```

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
