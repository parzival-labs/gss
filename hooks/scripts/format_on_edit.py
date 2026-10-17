#!/usr/bin/env python3
"""PostToolUse: run the project's formatter on the file just edited.

Opt-in. Set "format" in factory/config.json to a command containing {file},
for example "ruff format {file}" or "npx prettier --write {file}". Without
it this hook does nothing. A failing formatter is reported to Claude; the
edit itself has already happened.
"""

import os
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factory_state as fs  # noqa: E402


def run(data):
    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path")
    root = fs.repo_root(data.get("cwd"))
    if not path or not root:
        return 0, ""
    rel = fs.relpath_in_repo(root, path)
    template = fs.load_config(root).get("format")
    if rel is None or not isinstance(template, str) or "{file}" not in template:
        return 0, ""
    command = template.replace("{file}", shlex.quote(rel))
    try:
        result = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return 2, f"Formatter timed out after 60s: {command}"
    if result.returncode != 0:
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-20:])
        return 2, f"Formatter failed on {rel} (exit {result.returncode}): {command}\n{tail}"
    return 0, ""


if __name__ == "__main__":
    try:
        code, message = run(fs.read_hook_input(sys.stdin))
    except Exception as exc:
        code, message = 0, f"gss format_on_edit error, skipping: {exc}"
    if message:
        print(message, file=sys.stderr)
    sys.exit(code)
