"""Shared helpers for GSS Factory hooks. Python 3 standard library only.

Every hook fails open: if the repository state cannot be read, the hook
allows the action rather than block legitimate work on a hook bug.
"""

import fnmatch
import json
import os
import re
import subprocess

FACTORY_DIR = "factory"
BRANCH_PREFIX = "factory/"

TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs"}
TEST_FILE_PATTERNS = ["test_*", "*_test.*", "*.test.*", "*.spec.*", "*_spec.*", "*Test.java", "*Tests.cs"]


def git(root, *args):
    """Run git in root and return stripped stdout, or None on failure."""
    try:
        out = subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def git_ok(root, *args):
    try:
        return subprocess.run(
            ["git", "-C", root, *args], capture_output=True, timeout=10
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def repo_root(cwd):
    return git(cwd or os.getcwd(), "rev-parse", "--show-toplevel")


def current_branch(root):
    return git(root, "branch", "--show-current") or ""


def work_item_slug(root):
    """The slug of the work item whose branch is checked out, or None."""
    branch = current_branch(root)
    if branch.startswith(BRANCH_PREFIX) and len(branch) > len(BRANCH_PREFIX):
        return branch[len(BRANCH_PREFIX):]
    return None


def default_branch(root):
    ref = git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if ref:
        return ref.replace("refs/remotes/", "", 1)
    for name in ("main", "master", "origin/main", "origin/master"):
        if git_ok(root, "rev-parse", "--verify", "--quiet", name):
            return name
    return None


def branch_base(root):
    """The merge-base of HEAD with the default branch, or None."""
    default = default_branch(root)
    if not default:
        return None
    return git(root, "merge-base", "HEAD", default)


def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def frontmatter(text):
    """Parse flat key: value frontmatter between the first two --- lines."""
    if not text or not text.startswith("---"):
        return {}
    lines = text.splitlines()
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*(#.*)?$", line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def artifact_path(root, slug, name):
    return os.path.join(root, FACTORY_DIR, slug, name)


def artifact_status(root, slug, name):
    return frontmatter(read_text(artifact_path(root, slug, name))).get("status")


def plan_accepted(root, slug):
    return artifact_status(root, slug, "plan.md") == "accepted"


def load_config(root):
    text = read_text(os.path.join(root, FACTORY_DIR, "config.json"))
    if not text:
        return {}
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def relpath_in_repo(root, path):
    """Repository-relative path with forward slashes, or None if outside root."""
    if not path:
        return None
    path = path.replace("\\", "/")
    root_norm = os.path.realpath(root).replace("\\", "/")
    full = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path)).replace("\\", "/")
    if full == root_norm or not full.startswith(root_norm + "/"):
        return None
    return full[len(root_norm) + 1:]


def matches_any(relpath, patterns):
    return any(fnmatch.fnmatch(relpath, pattern) for pattern in patterns or [])


def is_test_file(relpath, extra_patterns=None):
    parts = relpath.split("/")
    if any(part in TEST_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    if any(fnmatch.fnmatch(name, pattern) for pattern in TEST_FILE_PATTERNS):
        return True
    return matches_any(relpath, extra_patterns)


def mentioned_in(text, relpath):
    return bool(text) and relpath in text


def read_hook_input(stream):
    try:
        data = json.load(stream)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}
