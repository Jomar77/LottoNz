Work through all unchecked items in PLAN.md sequentially, top to bottom.

For each item, follow the project's TDD cycle defined in CLAUDE.md:
1. Write failing tests that encode the item's acceptance criteria
2. Confirm the tests fail for the right reason
3. Implement the minimum code to make them pass
4. Run the FULL test suite, not just the new tests
5. Refactor if needed, keeping everything green
6. Commit with a descriptive conventional-commit message
7. Check off the item [x] in PLAN.md
8. Append progress to STATUS.md

Circuit breakers (per CLAUDE.md):
- If a test fails more than 3 times on the same fix, document in STATUS.md and move to the next item
- If a command errors more than 2 times consecutively, document and move on
- Never install a new dependency without noting it in STATUS.md first
- Never touch files outside this project directory
- Never read or print .env files or secrets

Before stopping for any reason (all items done, session limit, or a blocker),
write SESSION_NOTES.md summarising what was completed, decisions made, what
remains, and anything the human must review.
