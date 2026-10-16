---
name: factory-conventions
description: Conventions shared by every GSS Factory stage. Artifact layout under factory/<slug>/, frontmatter schema, stage order, gate rules and templates. Load when running or reasoning about any /gss command.
user-invocable: false
---

# GSS Factory conventions

The factory moves one unit of work, called a work item, around a loop. Each stage writes a markdown artifact, and a human accepts it before the next stage runs. Git is the only state store and the audit trail.

## Layout in the host repository

```
factory/
  README.md            index of work items, maintained by /gss:status
  <slug>/
    intent.md          what and why
    spec.md            requirements and constraints
    plan.md            files, order of work, tests, risks
    review.md          reviewer findings, ranked, with disposition
    log.md             one line per stage transition
  config.json          optional: {"checks": [...]} commands that must pass
```

`factory/config.json` is shared by all work items. Its `checks` array is the source of truth for what "checks pass" means. When it is absent, the plan's Checks section is used.

The slug is lower-case, hyphenated, at most five words, derived from the idea. `add-rate-limiting`, not `add_rate_limiting_to_the_public_api`.

## Stage order

| Stage | Produces | Next stage runs when |
|---|---|---|
| intent | `intent.md` | `intent.md` has `status: accepted` |
| spec | `spec.md` | `spec.md` has `status: accepted` |
| plan | `plan.md` | `plan.md` has `status: accepted` |
| build | commits on branch `factory/<slug>` and a `build:` line in `log.md` | the `build:` line says checks passed |
| review | `review.md` from the reviewer subagent and a `review:` line | the `review:` line says `0 important` |
| ship | a draft pull request and a `ship:` line in `log.md` | never; the PR merge is the final gate |

If a review has Important findings open, the next stage is build again, in fix mode, followed by a fresh review.

## Frontmatter

Every artifact begins with:

```yaml
---
stage: intent          # intent | spec | plan
status: draft          # draft | accepted | superseded
accepted_by:           # git user.name of the person who accepted
accepted_at:           # ISO date
ticket:                # optional external record ID
---
```

Flat key-value pairs only. No nesting, so a regex can parse it later.

## Gate rule

A stage ends by writing its artifact with `status: draft` and stopping with this message, adjusted for the stage:

> Written `factory/<slug>/intent.md`. Review it. To accept, set `status: accepted` in its frontmatter and commit, then run `/gss:factory <slug>` to continue.

If the user accepts in the conversation instead, in plain words such as "accept" or "looks good, go on", you may set `status: accepted`, fill `accepted_by` from `git config user.name` and `accepted_at` with today's date, and commit with the message `Accept <stage> for <slug>` quoting the user's words in the body. Never accept an artifact on your own judgement.

The gate is advisory in Iteration 0. A hook enforces it from Iteration 2.

## log.md

Append one line per transition, newest last:

```
2026-10-16 intent: drafted
2026-10-16 intent: accepted by Simon
2026-10-17 build: checks passed (3 passed, 0 failed) at a1b2c3d
2026-10-17 review: 1 important, 2 nits at a1b2c3d
2026-10-17 build: checks passed (4 passed, 0 failed) at e4f5a6b
2026-10-17 review: 0 important, 2 nits at e4f5a6b
2026-10-17 ship: draft PR #12
```

## Commits

Commit artifacts to the work item's branch `factory/<slug>`, created from the default branch at the start of the intent stage. One commit per artifact draft or acceptance. The build stage commits per plan step.

## Templates

Templates live next to this file under `templates/`, including `config.json` for projects that do not have one yet. Copy the whole template, keep every heading even if the answer is "none", and fill in the frontmatter.
