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

Iterations 1 and 2: feedback loop, separation of duties, and enforcement.

- A `verifier` subagent runs the checks in a fresh context before build is declared done.
- A `reviewer` subagent, which never sees the building session's reasoning, reviews every work item before it ships. Important findings send the work item back to build.
- An eval suite under `evals/` gates plugin changes in CI. See `evals/README.md`.

Iteration 2 adds hooks that enforce what the skills state: no code before an accepted plan, no quiet edits to existing tests, protected paths, a read-only reviewer, and no ending a build on unverified code. The `factory-conventions` skill lists what is enforced and what is still advisory. See `docs/DESIGN.md` for the iteration plan.
