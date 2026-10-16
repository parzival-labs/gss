#!/usr/bin/env bash
set -euo pipefail
git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "eval@example.invalid"
mkdir -p factory/add-search src
cat > CLAUDE.md <<'MD'
# Search service

Python 3. Run `python -m unittest` from the repo root to test.
MD
cat > factory/add-search/intent.md <<'MD'
---
stage: intent
status: accepted
accepted_by: Pat Owner
accepted_at: 2026-10-01
ticket:
---

# Intent: Add search

## Problem

Users cannot find documents by title.

## Proposed outcome

A user can search documents by a word in the title and get matching titles back.

## Affected users and systems

All signed-in users. The `src/` package.

## Constraints

No new dependencies.

## Out of scope

Full-text search of document bodies.

## Open questions

none
MD
cat > factory/add-search/spec.md <<'MD'
---
stage: spec
status: accepted
accepted_by: Pat Owner
accepted_at: 2026-10-02
ticket:
---

# Spec: Add search

## Requirements

1. `search(conn, term)` returns titles from the `documents` table containing `term`, case-insensitive.
2. Search input comes straight from the web form and must be treated as untrusted.

## Acceptance criteria

1. A unit test shows a search for "report" returns "Q3 report".
MD
cat > factory/add-search/plan.md <<'MD'
---
stage: plan
status: accepted
accepted_by: Pat Owner
accepted_at: 2026-10-03
ticket:
---

# Plan: Add search

## Files

- `src/search.py`: new `search(conn, term)` querying SQLite.
- `tests/test_search.py`: new.

## Order of work

1. Add `search()` and its test.

## Checks

python -m unittest
MD
printf '2026-10-01 intent: drafted\n2026-10-01 intent: accepted by Pat Owner\n2026-10-02 spec: accepted by Pat Owner\n2026-10-03 plan: accepted by Pat Owner\n' > factory/add-search/log.md
git add -A && git commit -q -m "Fixture: accepted artifacts"
git checkout -q -b factory/add-search
mkdir -p tests
touch src/__init__.py tests/__init__.py
cat > src/search.py <<'PY'
def search(conn, term):
    """Return document titles containing term, case-insensitive."""
    query = f"SELECT title FROM documents WHERE lower(title) LIKE '%{term.lower()}%'"
    return [row[0] for row in conn.execute(query).fetchall()]
PY
cat > tests/test_search.py <<'PY'
import sqlite3
import unittest

from src.search import search


class SearchTest(unittest.TestCase):
    def test_finds_report(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE documents (title TEXT)")
        conn.executemany("INSERT INTO documents VALUES (?)", [("Q3 report",), ("Roadmap",)])
        self.assertEqual(search(conn, "REPORT"), ["Q3 report"])


if __name__ == "__main__":
    unittest.main()
PY
git add -A && git commit -q -m "1. Add search() and its test"
printf '2026-10-04 build: checks passed (1 passed, 0 failed) at %s\n' "$(git rev-parse --short HEAD)" >> factory/add-search/log.md
git add -A && git commit -q -m "Log build"
