"""Tests for the GSS Factory hooks. Run: python3 -m unittest discover -s hooks/tests"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True)


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def plan(status, tests=""):
    return f"---\nstage: plan\nstatus: {status}\n---\n\n# Plan\n\n## Files\n\n- `src/app.py`\n\n## Tests\n\n{tests}\n"


class Repo:
    """A throwaway repo with main holding src/app.py and tests/test_app.py."""

    def __init__(self):
        self.root = os.path.realpath(tempfile.mkdtemp())
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.name", "Test")
        git(self.root, "config", "user.email", "test@example.invalid")
        write(self.root, "src/app.py", "x = 1\n")
        write(self.root, "tests/test_app.py", "assert True\n")
        self.commit("base")

    def commit(self, message):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message, "--allow-empty")

    def work_item(self, slug="add-thing", plan_status="draft", tests=""):
        git(self.root, "checkout", "-q", "-b", f"factory/{slug}")
        write(self.root, f"factory/{slug}/intent.md", "---\nstage: intent\nstatus: accepted\n---\n")
        write(self.root, f"factory/{slug}/plan.md", plan(plan_status, tests))
        write(self.root, f"factory/{slug}/log.md", "2026-10-17 plan: drafted\n")
        self.commit("artifacts")

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def run_hook(script, payload):
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


class GuardEditsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def edit(self, rel, tool="Edit"):
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        return run_hook("guard_edits.py", {
            "hook_event_name": "PreToolUse", "cwd": self.repo.root, "tool_name": tool,
            "tool_input": {key: os.path.join(self.repo.root, rel)},
        })

    def test_allows_everything_off_factory_branches(self):
        self.assertEqual(self.edit("src/app.py")[0], 0)

    def test_blocks_code_before_plan_accepted(self):
        self.repo.work_item(plan_status="draft")
        code, _, err = self.edit("src/app.py")
        self.assertEqual(code, 2)
        self.assertIn("no accepted plan", err)

    def test_blocks_notebook_before_plan_accepted(self):
        self.repo.work_item(plan_status="draft")
        self.assertEqual(self.edit("analysis.ipynb", tool="NotebookEdit")[0], 2)

    def test_allows_artifacts_before_plan_accepted(self):
        self.repo.work_item(plan_status="draft")
        self.assertEqual(self.edit("factory/add-thing/plan.md")[0], 0)
        self.assertEqual(self.edit("factory/README.md")[0], 0)

    def test_allows_code_after_plan_accepted(self):
        self.repo.work_item(plan_status="accepted")
        self.assertEqual(self.edit("src/app.py")[0], 0)

    def test_allows_new_test_file(self):
        self.repo.work_item(plan_status="accepted")
        self.assertEqual(self.edit("tests/test_new.py", tool="Write")[0], 0)

    def test_blocks_existing_test_not_in_plan(self):
        self.repo.work_item(plan_status="accepted")
        code, _, err = self.edit("tests/test_app.py")
        self.assertEqual(code, 2)
        self.assertIn("existing test", err)

    def test_allows_existing_test_named_in_plan(self):
        self.repo.work_item(plan_status="accepted", tests="Step 1 changes `tests/test_app.py`.")
        self.assertEqual(self.edit("tests/test_app.py")[0], 0)

    def test_blocks_protected_paths_on_any_branch(self):
        write(self.repo.root, "factory/config.json", json.dumps({"protected_paths": ["migrations/*"]}))
        self.repo.commit("config")
        code, _, err = self.edit("migrations/0001.sql", tool="Write")
        self.assertEqual(code, 2)
        self.assertIn("protected path", err)

    def test_blocks_config_edits_inside_work_item(self):
        write(self.repo.root, "factory/config.json", json.dumps({"checks": ["true"]}))
        self.repo.commit("config")
        self.repo.work_item(plan_status="accepted")
        self.assertEqual(self.edit("factory/config.json")[0], 2)

    def test_ignores_paths_outside_repo(self):
        self.repo.work_item(plan_status="draft")
        code, _, _ = run_hook("guard_edits.py", {
            "cwd": self.repo.root, "tool_name": "Write", "tool_input": {"file_path": "/tmp/elsewhere.txt"},
        })
        self.assertEqual(code, 0)

    def test_fails_open_on_garbage_input(self):
        result = subprocess.run([sys.executable, os.path.join(SCRIPTS, "guard_edits.py")],
                                input="not json", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
