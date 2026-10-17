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
PLAN_DRIFT = os.path.join(HERE, "..", "..", "bin", "gss-plan-drift")


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


class GuardReviewerBashTest(unittest.TestCase):
    def bash(self, command, agent_type="gss:reviewer"):
        return run_hook("guard_reviewer_bash.py", {
            "hook_event_name": "PreToolUse", "tool_name": "Bash", "agent_type": agent_type,
            "tool_input": {"command": command},
        })[0]

    def test_allows_read_only_git(self):
        for command in ["git diff main...HEAD", "git log --oneline -5", "git show HEAD:src/app.py",
                        "git -C /r status", "git branch", "git branch -a", "git branch --show-current"]:
            self.assertEqual(self.bash(command), 0, command)

    def test_accepts_unnamespaced_agent_type(self):
        self.assertEqual(self.bash("rm -rf src", agent_type="reviewer"), 2)

    def test_blocks_writes_and_chaining(self):
        for command in ["rm -rf src", "git checkout -- src", "git diff > out.txt", "git log; rm x", "git diff $(echo)",
                        "git diff --output=patch.txt", "git show --output patch.txt HEAD", "git diff --ext-diff",
                        "git branch evil", "git branch -D main", "git branch -m old new"]:
            self.assertEqual(self.bash(command), 2, command)

    def test_ignores_other_agents_and_main_session(self):
        self.assertEqual(self.bash("rm -rf build", agent_type="gss:verifier"), 0)
        self.assertEqual(self.bash("make test", agent_type=None), 0)


class DoneMeansCheckedTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def stop(self, active=False):
        code, out, _ = run_hook("done_means_checked.py", {
            "hook_event_name": "Stop", "cwd": self.repo.root, "stop_hook_active": active,
        })
        self.assertEqual(code, 0)
        return json.loads(out) if out.strip() else None

    def log(self, line):
        path = os.path.join(self.repo.root, "factory/add-thing/log.md")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def test_allows_off_factory_branches(self):
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.assertIsNone(self.stop())

    def test_allows_before_plan_accepted(self):
        self.repo.work_item(plan_status="draft")
        self.assertIsNone(self.stop())

    def test_allows_accepted_plan_with_no_code_yet(self):
        self.repo.work_item(plan_status="accepted")
        self.assertIsNone(self.stop())

    def test_blocks_uncommitted_code(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.assertEqual(self.stop()["decision"], "block")

    def test_blocks_code_committed_without_passing_build(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.repo.commit("1. change app")
        self.assertEqual(self.stop()["decision"], "block")

    def test_allows_after_passing_build_line(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.repo.commit("1. change app")
        self.log("2026-10-17 build: checks passed (1 passed) at abc123")
        self.repo.commit("Log build")
        self.assertIsNone(self.stop())

    def test_blocks_fix_after_build(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.repo.commit("1. change app")
        self.log("2026-10-17 build: checks passed at abc123")
        self.repo.commit("Log build")
        write(self.repo.root, "src/app.py", "x = 3\n")
        self.repo.commit("Fix review finding")
        self.assertEqual(self.stop()["decision"], "block")

    def test_allows_second_stop_attempt(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.assertIsNone(self.stop(active=True))


class FormatOnEditTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def edit(self, rel):
        return run_hook("format_on_edit.py", {
            "hook_event_name": "PostToolUse", "cwd": self.repo.root, "tool_name": "Edit",
            "tool_input": {"file_path": os.path.join(self.repo.root, rel)},
        })

    def test_noop_without_config(self):
        self.assertEqual(self.edit("src/app.py")[0], 0)

    def test_runs_configured_formatter_on_the_file(self):
        write(self.repo.root, "factory/config.json", json.dumps({"format": "echo formatted >> {file}"}))
        self.assertEqual(self.edit("src/app.py")[0], 0)
        with open(os.path.join(self.repo.root, "src/app.py"), encoding="utf-8") as fh:
            self.assertIn("formatted", fh.read())

    def test_reports_formatter_failure(self):
        write(self.repo.root, "factory/config.json", json.dumps({"format": "false {file}"}))
        code, _, err = self.edit("src/app.py")
        self.assertEqual(code, 2)
        self.assertIn("Formatter failed", err)


class PlanDriftTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def drift(self, *args):
        result = subprocess.run([sys.executable, PLAN_DRIFT, *args], cwd=self.repo.root,
                                capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout + result.stderr

    def test_clean_when_changes_are_planned(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/app.py", "x = 2\n")
        self.repo.commit("1. change app")
        code, out = self.drift()
        self.assertEqual(code, 0, out)

    def test_reports_unplanned_files(self):
        self.repo.work_item(plan_status="accepted")
        write(self.repo.root, "src/other.py", "y = 1\n")
        self.repo.commit("sneaky")
        code, out = self.drift()
        self.assertEqual(code, 1)
        self.assertIn("src/other.py", out)

    def test_needs_a_work_item(self):
        self.assertEqual(self.drift()[0], 2)


if __name__ == "__main__":
    unittest.main()
