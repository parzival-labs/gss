#!/usr/bin/env python3
"""Stop hook: do not end a build with unverified code on a work item branch.

On branch factory/<slug> with an accepted plan, Claude may not stop while
there are uncommitted code changes, or while the newest code commit on the
branch is newer than the newest `build: checks passed` line in log.md.

It nudges once per stop: when stop_hook_active is true it allows the stop,
so a genuine pause to ask the user a question is never trapped.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factory_state as fs  # noqa: E402

PASSED = "build: checks passed"


def decide(data):
    if data.get("stop_hook_active"):
        return None
    root = fs.repo_root(data.get("cwd"))
    if not root:
        return None
    slug = fs.work_item_slug(root)
    if not slug or not fs.plan_accepted(root, slug):
        return None

    exclude = f":(exclude){fs.FACTORY_DIR}"
    dirty = fs.git(root, "status", "--porcelain", "--", ".", exclude)
    if dirty:
        return (
            "There are uncommitted code changes on this work item. Commit the "
            "current plan step, then have the verifier run the checks and append "
            "a `build:` line to log.md. If you are pausing to ask the user "
            "something, say so and stop again."
        )

    base = fs.branch_base(root)
    rev_range = f"{base}..HEAD" if base else "HEAD"
    last_code = fs.git(root, "log", "-1", "--format=%H", rev_range, "--", ".", exclude)
    if not last_code:
        return None
    log_path = f"{fs.FACTORY_DIR}/{slug}/log.md"
    last_pass = fs.git(root, "log", "-1", "--format=%H", f"-G{PASSED}", rev_range, "--", log_path)
    if last_pass and fs.git_ok(root, "merge-base", "--is-ancestor", last_code, last_pass):
        return None
    return (
        "Code on this work item changed after the last `build: checks passed` "
        "line in log.md. Have the verifier run the checks and log the result "
        "before ending the build. If you are pausing to ask the user something, "
        "say so and stop again."
    )


def main():
    reason = decide(fs.read_hook_input(sys.stdin))
    if reason:
        print(json.dumps({"decision": "block", "reason": f"GSS Factory: {reason}"}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"gss done_means_checked error, allowing: {exc}", file=sys.stderr)
        sys.exit(0)
