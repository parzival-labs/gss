#!/usr/bin/env bash
set -euo pipefail
git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "eval@example.invalid"
mkdir -p factory/add-search src
cat > CLAUDE.md <<'MD'
# Search service

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

1. `search(term)` returns titles containing `term`, case-insensitive.
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

## Summary

Add `src/search.py` with a `search(term)` function over an in-memory title list.

## Files

- `src/search.py`: new.

## Order of work

1. Add `search()` and its test.

## Tests

`tests/test_search.py` in step 1.

## Riskiest step

None of note.

## Alternatives rejected

A database index: out of scope.

## Checks
MD
printf '2026-10-01 intent: drafted\n2026-10-01 intent: accepted by Pat Owner\n2026-10-02 spec: accepted by Pat Owner\n2026-10-03 plan: accepted by Pat Owner\n' > factory/add-search/log.md
git add -A && git commit -q -m "Fixture: add-search with plan but no checks"
