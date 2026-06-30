# Claude Code autonomous /yolo workflow — setup guide

A complete setup for running Claude Code overnight on a $20 Pro plan, working
through a task checklist with TDD, on an existing project. Sequential single-
session workflow (one terminal, one task list).

---

## What's in this package

```
CLAUDE.md                      ← coding laws + TDD + circuit breakers (commit this)
PLAN.md                        ← your nightly task checklist (commit this)
.claudeignore                  ← blocks secrets from Claude's view (commit this)
.claude/
  commands/yolo.md             ← the /yolo command (commit this)
  settings.json                ← wires the safety hook (commit this)
  safety_check.py              ← blocks dangerous bash commands (commit this)
gitignore-additions.txt        ← lines to append to your .gitignore (reference)
```

STATUS.md and SESSION_NOTES.md are created by Claude at runtime — you don't
write them, and they stay gitignored (per-machine).

---

## One-time setup (do this once on your existing project)

### 1. Copy the files into your project root

```bash
cd /path/to/your-project

# Copy from this package
cp /path/to/claude-setup/CLAUDE.md .
cp /path/to/claude-setup/PLAN.md .
cp /path/to/claude-setup/.claudeignore .
mkdir -p .claude/commands
cp /path/to/claude-setup/.claude/commands/yolo.md .claude/commands/
cp /path/to/claude-setup/.claude/settings.json .claude/
cp /path/to/claude-setup/.claude/safety_check.py .claude/
chmod +x .claude/safety_check.py
```

### 2. Fill in CLAUDE.md

Open CLAUDE.md and complete the three sections at the top:
- **Stack** — your runtime, framework, database, package manager
- **Conventions** — naming, commit style
- **How to run** — especially the test command. This is how Claude knows a
  task is actually done. Get this right.

Everything below the line is ready as-is (TDD rules, circuit breakers, security).

### 3. Update .gitignore

Append the lines from gitignore-additions.txt to your existing .gitignore.
This keeps STATUS.md / SESSION_NOTES.md per-machine and ensures secrets stay out.

### 4. Verify no API key is set

```bash
echo $ANTHROPIC_API_KEY
```

If this prints anything, unset it — otherwise Claude Code bills per-token via the
API instead of using your subscription:

```bash
unset ANTHROPIC_API_KEY
```

### 5. Confirm the hook works

```bash
echo '{"tool_input":{"command":"rm -rf /"}}' | python3 .claude/safety_check.py
echo "exit code: $?"   # should print 2 (blocked)

echo '{"tool_input":{"command":"npm test"}}' | python3 .claude/safety_check.py
echo "exit code: $?"   # should print 0 (allowed)
```

### 6. Commit the config

```bash
git add CLAUDE.md PLAN.md .claudeignore .claude/commands .claude/settings.json .claude/safety_check.py
git commit -m "chore: add Claude Code autonomous workflow config"
```

Setup done.

---

## Nightly rhythm

### 6pm — review yesterday, queue tonight (~20 min)

```bash
cat STATUS.md          # what got done overnight
cat SESSION_NOTES.md   # decisions + what to review
git log --oneline      # the commits
git diff               # the actual changes
```

Merge / keep what passes. Then rewrite PLAN.md with tonight's 3-5 tasks. Each task:
- One self-contained deliverable
- An explicit `Acceptance:` line (Claude's done signal)
- TDD steps noted in the description

### 10pm (or whenever) — launch and walk away

```bash
cd /path/to/your-project
claude --dangerously-skip-permissions
```

Then inside Claude:

```
/yolo
```

`/yolo` takes no arguments. It reads PLAN.md and works through it. Close nothing,
leave the terminal open, walk away.

### Morning — quick async check

```bash
cat SESSION_NOTES.md
git log --oneline
```

Unchecked `[ ]` items in PLAN.md roll into tonight's queue.

---

## How the pieces fit

- **CLAUDE.md** loads on every session start. TDD and circuit breakers are
  always in effect — you never re-state them.
- **PLAN.md** is the only thing you edit nightly. The task list.
- **/yolo** reads PLAN.md, applies CLAUDE.md's rules, works top to bottom.
- **STATUS.md / SESSION_NOTES.md** are Claude's output — your morning read.
- **.claudeignore + hook + .gitignore** are five layers keeping secrets safe
  and destructive commands blocked while you sleep.

---

## Limits to remember ($20 Pro)

- 5-hour rolling session window — the session pauses when hit; files are safe.
- 200K context window; auto-compacts around 83% and keeps going.
- Weekly cap shared across Claude Code, Claude.ai chat, and Cowork.
- Keep CLAUDE.md under 200 lines — it's a token tax on every turn.
- Use Sonnet as default; reach for Opus only on hard architecture.

---

## First night advice

Start with 2-3 small, low-risk tasks so you can calibrate how much Claude gets
through in one session before trusting it with bigger chunks. Read the morning
diff carefully the first few times — you're learning to write tasks Claude can
execute cleanly, and the feedback loop is the diff.
