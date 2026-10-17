---
name: plan
description: Plan stage of the GSS Factory. Reads an accepted factory/<slug>/spec.md and writes plan.md naming files, order of work, tests, the riskiest step and rejected alternatives. Read-only until the plan is written. Use for /gss:plan.
argument-hint: <slug>
---

# /gss:plan

Read the `factory-conventions` skill. Input is an accepted `factory/<slug>/spec.md`. Output is `factory/<slug>/plan.md` from `templates/plan.md`.

## Steps

1. Refuse to start if `spec.md` is missing or still `draft`.
2. Enter plan mode if the `EnterPlanMode` tool is available. No file outside `factory/<slug>/` may change during this stage. Enforced: the `guard_edits` hook blocks any other edit on branch `factory/<slug>` until plan.md is accepted.
3. Read `spec.md`. Delegate exploration to the `researcher` subagent, giving it the slug and `spec.md`, then read the files it names: every file the change touches, its tests, how it is built and checked.
4. Draft the plan. Every requirement in the spec must be covered by at least one step. Every step must be one commit that leaves the checks green.
5. Ask the engineer the three questions, all at once, and fold the answers in:
   - What could this break?
   - Which step is the riskiest?
   - Which alternative did we reject, and would you have chosen differently?
6. Fill the Checks section with the exact commands from `factory/config.json` if it exists, else from the project's `CLAUDE.md`. If neither names any, ask for them now and offer to create `factory/config.json` from the template so every later work item reuses them. The build stage will not run without checks.
7. Exit plan mode if you entered it. Write `plan.md` with `status: draft`, append `plan: drafted` to `log.md`, commit as `Draft plan for <slug>`.
8. Stop with the gate message.

Done when someone who never saw this conversation could implement from `plan.md` alone.
