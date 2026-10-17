---
name: factory
description: Run the GSS Factory on a unit of work. Finds or creates the work item under factory/<slug>/, reads its artifacts to work out the current stage, runs the next stage, and stops at the gate. Use for "take this idea through the factory", "continue <slug>", or any /gss:factory request.
argument-hint: <idea or slug>
---

# /gss:factory

You are the orchestrator. Read the `factory-conventions` skill first. Then:

## 1. Resolve the work item

- If `$ARGUMENTS` matches an existing directory `factory/<slug>/`, that is the work item.
- Otherwise `$ARGUMENTS` is a new idea. Derive a slug per the conventions and go straight to the intent stage's questions in the same reply. State the proposed slug in one line at the top so the user can correct it when they answer. Do not spend a round trip on the slug alone. Create nothing until the user has answered.
- If `$ARGUMENTS` is empty, run `/gss:status` behaviour and ask which work item to continue.

## 2. Work out the current stage

Read the frontmatter of each artifact that exists and `log.md`. Apply the first matching row:

| Observation | Action |
|---|---|
| no `intent.md` | run the intent stage |
| `intent.md` is `draft` | stop: waiting for acceptance of intent |
| `intent.md` accepted, no `spec.md` | run the spec stage |
| `spec.md` is `draft` | stop: waiting for acceptance of spec |
| `spec.md` accepted, no `plan.md` | run the plan stage |
| `plan.md` is `draft` | stop: waiting for acceptance of plan |
| `plan.md` accepted, no `build:` line saying checks passed | run the build stage |
| newest `build:` line says failed | run the build stage |
| newest `build:` line passed and is newer than any `review:` line | run the review stage |
| newest `review:` line has more than `0 important` | run the build stage in fix mode |
| newest `review:` line says `0 important`, no `ship:` line | run the ship stage |
| `ship:` line present | report the PR and stop |

"Newer" means later in `log.md`.

"Stop: waiting" means tell the user which file to review and how to accept it, per the gate rule. If their message already accepts it in plain words, apply the acceptance per the conventions and continue to the next row.

## 3. Run exactly one stage

Load the matching stage skill with the Skill tool, by its namespaced name: `gss:intent`, `gss:spec`, `gss:plan`, `gss:build`, `gss:review` or `gss:ship`. Then follow it exactly. Never run a stage from this table alone or from memory: the stage skill holds its limits, such as how many questions to ask. Do not run two stages in one invocation, even if the user accepted in chat. One stage, one gate, one stop. The user runs `/gss:factory <slug>` again to continue.

## 4. Before stopping

- Append the transition to `factory/<slug>/log.md`.
- Commit on branch `factory/<slug>`.
- Print the gate message.

The one-stage rule is advisory. The gates are partly enforced: hooks stop any code changing before the plan is accepted. See the enforcement table in `factory-conventions`.
