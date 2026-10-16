# GSS

Gregarious Simulation Systems. Home of the GSS Factory: an agentic software factory for Claude Code, built here and distributed as a plugin.

The factory walks a unit of work around the loop from Anthropic's AI-native SDLC playbook. Each stage writes a markdown artifact under `factory/<slug>/`, and a human accepts it before the next stage runs. Git is the audit trail.

```
idea -> intent.md -> spec.md -> plan.md -> build -> review.md -> draft PR
         [gate]      [gate]     [gate]   [verifier] [reviewer]  [gate: merge]
```

## Install

```
/plugin marketplace add parzival-labs/gss
/plugin install gss@gss
```

Or, from a checkout of this repo, `claude --plugin-dir .`

## Use

```
/gss:factory "describe the change you want"
```

Review the artifact it writes, set `status: accepted` in its frontmatter, commit, and run the same command again to continue. `/gss:status` shows every work item and what it is waiting on. The stage commands `/gss:intent`, `/gss:spec`, `/gss:plan`, `/gss:build`, `/gss:review` and `/gss:ship` run one stage on their own.

Put the commands that must pass in `factory/config.json`, for example `{"checks": ["make test"]}`. The build stage will not start without checks.

## Status

Iteration 1: feedback loop and separation of duties.

- A `verifier` subagent runs the checks in a fresh context before build is declared done.
- A `reviewer` subagent, which never sees the building session's reasoning, reviews every work item before it ships. Important findings send the work item back to build.
- An eval suite under `evals/` gates plugin changes in CI. See `evals/README.md`.

Hooks that enforce the rules the skills state arrive in Iteration 2. See `docs/DESIGN.md` for the iteration plan.
