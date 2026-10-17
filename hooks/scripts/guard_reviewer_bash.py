#!/usr/bin/env python3
"""PreToolUse guard for Bash inside the reviewer subagent.

The reviewer may only run read-only git commands, one at a time. This keeps
the separation of duties real: the agent reviewing a change cannot alter it.
Bash in every other context is untouched.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factory_state as fs  # noqa: E402

REVIEWER_TYPES = {"reviewer", "gss:reviewer"}
ALLOWED = re.compile(r"^\s*git\s+(?:-C\s+\S+\s+)?(diff|log|show|branch|status|rev-parse|merge-base|ls-files|blame)\b")
SHELL_META = re.compile(r"[;&|`<>]|\$\(|\n")


WRITING_FLAGS = ("--output", "--ext-diff")
BRANCH_READ_FLAGS = {"-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "--list", "-l", "--show-current", "--no-color"}


def read_only(command):
    match = ALLOWED.match(command)
    if not match or SHELL_META.search(command):
        return False
    tokens = command.split()
    if any(token.startswith(WRITING_FLAGS) for token in tokens):
        return False
    if match.group(1) == "branch":
        after = tokens[tokens.index("branch") + 1:]
        if any(token not in BRANCH_READ_FLAGS for token in after):
            return False
    return True


def decide(data):
    if data.get("agent_type") not in REVIEWER_TYPES:
        return None
    command = (data.get("tool_input") or {}).get("command") or ""
    if read_only(command):
        return None
    return (
        "The reviewer is read-only. It may run single git commands such as "
        "`git diff`, `git log` or `git show`, with no pipes, redirects or chaining. "
        "Report what you need checked as a finding instead."
    )


def main():
    reason = decide(fs.read_hook_input(sys.stdin))
    if reason:
        print(f"GSS Factory blocked this command. {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"gss guard_reviewer_bash error, allowing: {exc}", file=sys.stderr)
        sys.exit(0)
