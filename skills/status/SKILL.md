---
name: status
description: List GSS Factory work items and their current stage, and refresh factory/README.md. Use for "where are we", "factory status", or /gss:status.
argument-hint: [slug]
allowed-tools: Read, Glob, Grep, Write(factory/README.md), Bash(git log *), Bash(git branch *)
---

# /gss:status

Read the `factory-conventions` skill.

1. List every directory under `factory/` that contains an `intent.md`. With a slug argument, show only that one.
2. For each, read the frontmatter of the artifacts present and the last line of `log.md`. Derive the stage with the same table `/gss:factory` uses.
3. Print a table:

   | Work item | Stage | Waiting on | Last activity |
   |---|---|---|---|

   "Waiting on" is `acceptance of <artifact>`, `build`, `fixes for <n> Important findings`, `review`, `ship`, `PR #n review`, or `done`.
4. Rewrite `factory/README.md` with the same table under a one-line heading, so the index is browsable on GitHub. Do not commit; the next stage commit will carry it.

No model judgement is needed for this skill. If anything is ambiguous, say so in the table rather than guessing.
