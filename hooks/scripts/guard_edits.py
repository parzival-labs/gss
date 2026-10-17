#!/usr/bin/env python3
"""PreToolUse guard for Write, Edit, MultiEdit and NotebookEdit.

Blocks, with exit code 2 and a reason on stderr:
  1. Edits to paths listed in protected_paths in factory/config.json.
  2. Edits to factory/config.json itself while a work item branch is out.
  3. Edits outside factory/<slug>/ before that work item's plan.md is accepted.
  4. Edits to tests that already exist on the default branch during build,
     unless plan.md names the test file.

Anything it cannot evaluate is allowed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factory_state as fs  # noqa: E402


def decide(data):
    """Return a block reason, or None to allow."""
    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    root = fs.repo_root(data.get("cwd"))
    if not path or not root:
        return None
    rel = fs.relpath_in_repo(root, path)
    if rel is None:
        return None

    config = fs.load_config(root)
    slug = fs.work_item_slug(root)

    protected = config.get("protected_paths") or []
    if fs.matches_any(rel, protected):
        return (
            f"`{rel}` is a protected path in factory/config.json. "
            "Changes to it need a human: ask the user to make this edit, "
            "or to approve removing the path from protected_paths in a reviewed commit."
        )

    if slug and rel == f"{fs.FACTORY_DIR}/config.json":
        return (
            "factory/config.json defines the factory's checks and protected paths, "
            "so it cannot change inside a work item. Change it in its own reviewed PR."
        )

    if not slug:
        return None

    item_dir = f"{fs.FACTORY_DIR}/{slug}/"
    if rel.startswith(item_dir) or rel == f"{fs.FACTORY_DIR}/README.md":
        return None

    if not os.path.isdir(os.path.join(root, fs.FACTORY_DIR, slug)):
        return None

    if not fs.plan_accepted(root, slug):
        return (
            f"Work item `{slug}` has no accepted plan yet, so only files under "
            f"{item_dir} may change. Finish and accept plan.md first: a human sets "
            "`status: accepted` in its frontmatter and commits."
        )

    if fs.is_test_file(rel, config.get("test_globs")):
        base = fs.branch_base(root)
        existed = bool(base) and fs.git_ok(root, "cat-file", "-e", f"{base}:{rel}")
        plan_text = fs.read_text(os.path.join(root, item_dir, "plan.md"))
        if existed and not fs.mentioned_in(plan_text, rel):
            return (
                f"`{rel}` is an existing test and plan.md does not list it. "
                "Fix the code, not the test. If the plan really needs this test to "
                f"change, add `{rel}` to the Tests section of plan.md in the same "
                "commit and say why, so the reviewer sees it."
            )
    return None


def main():
    reason = decide(fs.read_hook_input(sys.stdin))
    if reason:
        print(f"GSS Factory blocked this edit. {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail open on hook bugs
        print(f"gss guard_edits error, allowing: {exc}", file=sys.stderr)
        sys.exit(0)
