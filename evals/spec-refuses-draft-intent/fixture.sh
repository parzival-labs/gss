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
status: draft
accepted_by: 
accepted_at: 
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
printf '2026-10-01 intent: drafted\n' > factory/add-search/log.md
git add -A && git commit -q -m "Fixture: add-search with draft intent"
