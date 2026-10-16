# GSS

Gregarious Simulation Systems. Home of the GSS Factory: an agentic software factory for Claude Code, built here and distributed as a plugin.

The factory walks a unit of work around the loop from Anthropic's AI-native SDLC playbook. Each stage writes a markdown artifact under `factory/<slug>/`, and a human accepts it before the next stage runs. Git is the audit trail.

```
idea -> intent.md -> spec.md -> plan.md -> commits + checks -> draft PR
         [gate]      [gate]     [gate]                        [gate: merge]
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

Review the artifact it writes, set `status: accepted` in its frontmatter, commit, and run the same command again to continue. `/gss:status` shows every work item and what it is waiting on. The stage commands `/gss:intent`, `/gss:spec`, `/gss:plan`, `/gss:build` and `/gss:ship` run one stage on their own.

## Status

Iteration 0: walking skeleton. Skills and templates only, human at every gate, no hooks or subagents yet. See `docs/DESIGN.md` for the design and the iteration plan.
