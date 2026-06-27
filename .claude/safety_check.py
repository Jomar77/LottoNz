#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code.
Reads the proposed Bash command from stdin (JSON) and blocks dangerous ones.
Exit code 2 = block the command and feed the reason back to Claude.
Exit code 0 = allow.
"""
import json
import sys
import re

# Patterns that should never run during an autonomous session.
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",          # rm -rf /
    r"rm\s+-rf\s+~",          # rm -rf ~
    r"rm\s+-rf\s+\$HOME",     # rm -rf $HOME
    r"rm\s+-rf\s+\*",         # rm -rf *
    r"git\s+push\s+.*--force", # force push
    r"git\s+push\s+.*-f\b",    # force push short flag
    r"drop\s+database",        # SQL drop database
    r"drop\s+table",           # SQL drop table
    r"cat\s+.*\.env",          # reading .env
    r"printenv",               # dumping env
    r"\benv\b\s*\|",           # env | ...
    r"echo\s+\$[A-Z_]*KEY",    # echoing secret-ish vars
    r"echo\s+\$[A-Z_]*SECRET",
    r"echo\s+\$[A-Z_]*TOKEN",
    r"~/\.ssh",                # ssh keys
    r"~/\.aws",                # aws creds
    r"/etc/",                  # system config
    r":\(\)\{.*\}",            # fork bomb
]


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # If we can't parse, fail safe by allowing (Claude's own rules still apply).
        sys.exit(0)

    command = ""
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")

    lowered = command.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lowered):
            print(
                f"BLOCKED by safety_check.py: command matches forbidden pattern '{pattern}'. "
                f"Document this in STATUS.md and choose a safe alternative.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
