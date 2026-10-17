# GSS Factory: design proposal

Status: proposal, v0.1 (2026-10-16)
Scope: an agentic software factory, invoked from a slash command in Claude Code, built in this repo and distributed as a plugin.

## 1. Summary

The factory is a Claude Code plugin named `gss`. Its main entry point is one slash command, `/gss:factory`, which drives a unit of work around the loop described in Anthropic's AI-native SDLC playbook:

```
idea ──> intent.md ──> spec.md ──> plan.md ──> diff + tests ──> PR with review findings ──> (incident) ──> intent.md
          [gate]        [gate]      [gate]        [checks]          [gate: human merge]
```

Every stage ends by committing a markdown artifact that the next stage reads. Humans own the gates. Git is the audit trail. The factory itself is just skills, subagents, hooks and a few shell scripts, so the first version is almost entirely markdown and can be built in days.

We build it in iterations. Iteration 0 is a walking skeleton that runs the whole loop with a human at every gate and no automation. Each later iteration moves one more piece of enforcement from "the skill asks nicely" to "a hook or CI check guarantees it". The factory is dogfooded from the first commit: the first `intent.md` in this repo describes the factory.

## 2. What the playbook says, condensed

Source: https://claude.com/resources/articles/the-ai-native-sdlc-playbook

Core thesis:

- Code is no longer the bottleneck. Plan, review and deploy are, because they still run at human speed.
- The AI-native SDLC is a loop, not a line. Each stage commits an artifact the next stage reads: `intent.md` -> `spec.md` -> `plan.md` -> diff and tests -> PR with review findings -> incident record -> new `intent.md`.
- Humans keep accountability for judgment. Their attention moves from producing artifacts to reviewing what agents flag at each gate.
- Git history is the audit trail: who asked for what, what the agent produced, who approved it.

Principles we adopt directly:

| Principle | How the factory honours it |
|---|---|
| Each stage commits an artifact the next reads | Fixed artifact set per work item under `factory/<slug>/` |
| Humans own judgment; agents act up to gates they cannot pass | Explicit accept step after intent, spec and plan; human merges the PR |
| Skills are advisory; hooks and checks enforce | Every rule a skill states gets a deterministic backstop in a later iteration |
| Separation of duties | The session that wrote the code never approves it; a fresh-context reviewer agent reviews it |
| Give Claude a feedback loop | Build stage runs the project's own checks and pastes output before declaring done |
| Configuration is tested like code | Plugin eval suite runs on every change to skills, agents and hooks |
| Detection is deterministic; models diagnose | Maintain stage (later iteration) triggers from scripts, never from a model |

Playbook features the factory uses: plan mode, `CLAUDE.md`, skills, hooks (`PreToolUse` exit code 2), subagents with tool limits, worktrees, headless `claude -p`, `claude-code-action`, `REVIEW.md`, plugin evals.

## 3. Design goals and non-goals

Goals:

1. One command to start a unit of work from an idea, and one command to resume it from wherever it stopped.
2. Artifacts are plain markdown in the target repo. No database, no service, no state outside git.
3. Works in any project the plugin is installed in, with zero required configuration. Optional configuration lives in one file.
4. Every rule is first written as skill guidance, then hardened by a hook or check once it has proven worth enforcing.
5. The factory can run its own loop on itself.

Non-goals for now:

- Replacing Jira, Linear or other trackers. The playbook's "linkage as minimum" rule applies: an artifact may carry a ticket ID, and that is all.
- Multi-repo orchestration. One repo, one work item, one branch.
- Production deployment. The factory stops at a mergeable PR. Deploy and Maintain plays come after the build loop is solid.

## 4. The shape of the plugin

### 4.1 Commands

All commands are skills in `skills/<name>/SKILL.md`, which Claude Code exposes as `/gss:<name>` once the plugin is installed.

| Command | Stage | What it does | Ends with |
|---|---|---|---|
| `/gss:factory <idea or slug>` | all | Orchestrator. Finds or creates the work item, reads its artifacts, works out the current stage, and runs the next stage. Stops at every gate. | The next gate |
| `/gss:intent <idea>` | Plan | Analyst-style questioning (scope, users, constraints, success), then writes `intent.md` from the template. | `intent.md` draft |
| `/gss:spec <slug>` | Design | Turns an accepted `intent.md` into `spec.md`. Names constraints, flags concerns, lists open questions. Loads project policy skills if present. | `spec.md` draft |
| `/gss:plan <slug>` | Build | Read-only. Produces `plan.md` naming files, order of work, tests, risks and rejected alternatives. Good enough that someone who never saw the conversation could implement it. | `plan.md` draft |
| `/gss:build <slug>` | Build + Test | Implements `plan.md` on a branch. Runs the project's checks after each step. Keeps `plan.md` in sync when reality diverges. | Diff and passing checks |
| `/gss:review <slug>` | Deploy | Fresh-context reviewer subagent checks the diff against `spec.md`, `plan.md` and `REVIEW.md`. Findings ranked Important / Nit. | `review.md` |
| `/gss:ship <slug>` | Deploy | Pushes the branch and opens a draft PR whose body links the artifacts and pastes the check output. | Draft PR |
| `/gss:status [slug]` | any | Lists work items and their stage. No model calls beyond reading files. | Table |

`/gss:factory` is the only command most people need. The stage commands exist so a stage can be re-run on its own and so CI can call one stage headlessly.

### 4.2 Artifacts in the target repo

```
factory/
  README.md              index of work items, maintained by /gss:status
  config.json            optional: check commands, protected paths, risk tiers
  <slug>/
    intent.md            problem, proposed outcome, affected users and systems, constraints, open questions
    spec.md              requirements, constraints applied, concerns flagged, acceptance criteria
    plan.md              files, order of work, tests, riskiest step, rejected alternatives
    review.md            reviewer findings, ranked, with disposition
    log.md               one line per stage transition: when, who accepted, commit
```

Each artifact starts with frontmatter:

```yaml
---
stage: intent          # intent | spec | plan | build | review | shipped
status: draft          # draft | accepted | superseded
accepted_by:           # git author of the accepting commit
accepted_at:
ticket:                # optional external record ID (playbook "linkage as minimum")
---
```

The frontmatter is the factory's only state. `/gss:factory` reads it to decide what to do next. Accepting an artifact means editing `status: accepted` and committing. That commit is the audit record.

### 4.3 Subagents

Defined in `agents/*.md`, each with a narrow tool list and a fresh context window:

| Agent | Tools | Purpose |
|---|---|---|
| `researcher` | Read, Grep, Glob | Explores the codebase for spec and plan stages, reports back, never edits |
| `verifier` | Read, Bash (checks only) | Runs the checks and the app after build, reports pass/fail with literal output, never fixes |
| `reviewer` | Read, Grep, Glob, Bash (git diff) | Reviews the diff against spec, plan and REVIEW.md. Never edits. This is the separation-of-duties agent |
| `simplifier` | Read, Edit | Runs after build to remove duplication and over-engineering within the plan's scope |

### 4.4 Hooks

Hooks are the deterministic layer, built in Iteration 2. All are stdlib Python under `hooks/scripts/`, tested in `hooks/tests/`, and fail open: if a hook cannot read the repository state, it allows the action rather than block work on a hook bug.

| Hook | Event | Rule |
|---|---|---|
| `guard_edits` | PreToolUse on Write, Edit, MultiEdit, NotebookEdit | On branch `factory/<slug>`: no edits outside `factory/<slug>/` until plan.md is accepted; no edits to tests that exist on the default branch unless plan.md names them; no edits to `factory/config.json`. On any branch: no edits to `protected_paths` from the config |
| `guard_reviewer_bash` | PreToolUse on Bash | Inside the reviewer subagent only, allow single read-only git commands and nothing else |
| `done_means_checked` | Stop | On a work item with an accepted plan, block once if code is uncommitted or newer than the last `build: checks passed` line. A second stop is always allowed, so a genuine pause to ask the user is never trapped |
| `format_on_edit` | PostToolUse on Write, Edit, MultiEdit | Opt-in: run the `format` command from the config on the edited file |

Each block message explains the reason and the route to approval, as the playbook requires.

Two changes from the original plan. The "plan stage" guard keys on the work item branch and plan.md's status rather than a stage marker, so it needs no extra state. The "tests during a fix" guard became "existing tests during build", because a review fix sometimes legitimately adds tests: new test files are always allowed, and changing an existing one means naming it in plan.md, where the reviewer sees it.

`bin/gss-plan-drift` is a command rather than a hook. The ship stage runs it, and it fails when the branch changes a file that plan.md does not name.

### 4.5 Knowledge skills

Non-invocable skills (`user-invocable: false`) that carry the factory's institutional knowledge so the stage skills stay short:

- `factory-conventions`: artifact templates, frontmatter schema, directory layout, gate rules.
- The review passes and Important / Nit definitions live in the `reviewer` agent itself, so there is one place to edit them.

Project-specific policy skills (security standard, API conventions, brand rules) are not part of the plugin. The spec and review stages load whatever skills the host project provides.

## 5. The loop in detail

What happens on `/gss:factory "add rate limiting to the public API"`:

1. **Locate.** Slugify the idea, look for `factory/add-rate-limiting/`. Not found, so create it.
2. **Intent.** Ask the analyst questions. Write `intent.md` with `status: draft`. Stop: "Review `factory/add-rate-limiting/intent.md`. Run `/gss:factory add-rate-limiting` again when it is accepted."
3. **Gate.** The human edits, sets `status: accepted`, commits.
4. **Spec.** On re-run, the orchestrator sees an accepted intent and no spec. The `researcher` agent maps the relevant code. The spec is written against the project's policy skills, with concerns flagged at the top. Stop at the gate.
5. **Plan.** On re-run, enter plan mode, read the spec and the codebase, write `plan.md`. The skill asks the engineer the playbook's three questions: what could break, which step is riskiest, what was rejected. Stop at the gate.
6. **Build.** On re-run, create branch `factory/add-rate-limiting`, implement step by step. After each step run the check command from `factory/config.json` or the project's `CLAUDE.md`. If the plan changes, edit `plan.md` in the same commit. Run `simplifier`, then `verifier`. Paste verifier output into `log.md`.
7. **Review.** `reviewer` agent, fresh context, produces `review.md`. Important findings are fixed in the same session and re-verified. Nits are listed with a disposition.
8. **Ship.** Push, open a draft PR. Body: links to the four artifacts, verifier output, review summary. The human reviews intent and risk, not every line, and merges. The merge is the final gate.
9. **Close the loop.** Anything learned twice goes into the host project's `CLAUDE.md`. Any escaped defect becomes a new eval case and, if large, a new `intent.md`.

Each stage runs in whichever session the human is in. Nothing requires the same session to survive from intent to ship, because all state is in the artifacts.

## 6. Iteration plan

Start simple, make it work end to end, then harden one layer at a time.

### Iteration 0: walking skeleton

Goal: run the whole loop on a toy change in this repo, with a human at every gate.

- Plugin scaffold: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` with `"source": "."`, so this repo is both plugin and marketplace.
- Skills: `factory`, `intent`, `spec`, `plan`, `build`, `ship`, `status`, plus `factory-conventions`.
- Artifact templates.
- `CLAUDE.md` for this repo, under a page.
- `factory/gss-factory/intent.md`: the factory's own intent, written with `/gss:intent`.
- No subagents, no hooks, no CI. `claude plugin validate .` passes.

Done when: a contributor installs the plugin from GitHub and takes a small change through to a draft PR using only `/gss:factory`.

### Iteration 1: feedback loop and separation of duties

- `verifier` and `reviewer` subagents. `/gss:review` command.
- `factory/config.json` with a `checks` list. Build stage refuses to call itself done without green checks.
- Eval suite v0: five cases under `evals/` covering intent questioning, spec concern flagging, plan completeness, build honesty about failing checks, and review ranking. Run with `claude plugin eval`.
- GitHub Actions workflow: `claude plugin validate` and `claude plugin eval` on changes to `skills/**`, `agents/**`, `hooks/**`.

Done when: a review finding has been caught by `reviewer` that the building session missed, and the eval suite gates a plugin PR.

### Iteration 2: deterministic guardrails

- `hooks/hooks.json` with the hooks in 4.4, each a small Python script under `hooks/scripts/`, each with its own test. Built.
- `researcher` and `simplifier` subagents. Built.
- Plan-drift check: `/gss:ship` fails if the diff touches files that `plan.md` does not mention, unless `plan.md` was updated in the branch. Built as `bin/gss-plan-drift`.
- Risk tiers in `config.json`: `low` work items skip the plan gate, `high` ones require a named second approver in `accepted_by`. Deferred: this is an open question in the factory's own intent, and it needs a decision on who sets the tier.

Done when: every rule written in a skill in Iterations 0 and 1 has a hook or check behind it, or a recorded decision that it stays advisory.

### Iteration 3: headless stages and the PR loop

- `claude-code-action` workflows in the host repo, installed by `/gss:init`: on merge of an `intent.md`, open a `spec.md` PR; on merge of a `plan.md`, optionally run build in a sandboxed job and open the draft PR.
- `REVIEW.md` template and PR review via the action or the managed Code Review service.
- `/gss:sweep <pr>`: for factory-authored PRs, address unresolved review comments and failing checks until green and awaiting approval.
- Metrics script: reads git history and reports the playbook's leading indicators (time from first `intent.md` commit to accepted, intent to spec, plan to merged PR, first-pass CI rate).

Done when: a work item has gone from accepted intent to draft PR with no interactive session.

### Iteration 4: maintain and close the loop

- Detection script with bands (`bands.yml`), unit-tested, no model in the detection path.
- Tiered response: log, diagnose read-only, open PR into the review gate.
- Diagnosis written as a new `intent.md`, which starts the loop again.
- Recurring scan hook-in (Claude Security or scheduled `claude -p`), findings routed to `intent.md`.

## 7. Repository layout (this repo)

```
gss/
  .claude-plugin/
    plugin.json            name: gss, version, description, author
    marketplace.json       name: gss, plugins: [{ name: gss, source: "." }]
  skills/
    factory/SKILL.md       orchestrator            -> /gss:factory
    intent/SKILL.md                                 -> /gss:intent
    spec/SKILL.md                                   -> /gss:spec
    plan/SKILL.md                                   -> /gss:plan
    build/SKILL.md                                  -> /gss:build
    review/SKILL.md        (iteration 1)            -> /gss:review
    ship/SKILL.md                                   -> /gss:ship
    status/SKILL.md                                 -> /gss:status
    init/SKILL.md          (iteration 3)            -> /gss:init
    factory-conventions/   knowledge skill, not user-invocable
      SKILL.md
      templates/intent.md, spec.md, plan.md, review.md, config.json
  agents/                  (iteration 1+)
    researcher.md  verifier.md  reviewer.md  simplifier.md
  hooks/                   (iteration 2)
    hooks.json
    scripts/*.sh  tests/*.sh
  evals/                   (iteration 1)
    <case>/prompt.md  <case>/graders/*.md
  .github/workflows/
    plugin-ci.yml          validate + eval on plugin changes
  factory/                 dogfood: the factory's own work items
    gss-factory/intent.md
  docs/
    DESIGN.md              this document
  CLAUDE.md
  README.md                install and quick start
```

Install in another project:

```
/plugin marketplace add parzival-labs/gss
/plugin install gss@gss
/gss:factory "describe the change"
```

## 8. Mechanics verified against the current docs

These shape the design and are worth knowing before building. Verified on 2026-10-16 against code.claude.com/docs with Claude Code 2.1.301 installed here.

- Slash commands are skills. `skills/<name>/SKILL.md` in plugin `gss` becomes `/gss:<name>`. The older `commands/*.md` form still works but the docs say to prefer skills.
- A plugin cannot set the permission mode, and `permissionMode` in a plugin-shipped agent is ignored. So the plan stage cannot force plan mode. The skill asks Claude to call `EnterPlanMode`, and the `guard_edits` hook is the enforcement. This is exactly the playbook's "skills advise, hooks enforce".
- A `CLAUDE.md` inside a plugin is not loaded. Factory conventions therefore live in a knowledge skill, which is also what the playbook recommends for institutional knowledge.
- Plugin hooks live in `hooks/hooks.json`. Exit code 2 blocks and feeds stderr to Claude. Use the `args` exec form with `${CLAUDE_PLUGIN_ROOT}` for script paths.
- `claude plugin validate <path>` checks structure. `claude plugin eval` runs `evals/<case>/prompt.md` with graders and supports `--trust-plugin` and `--json` for CI. Every eval run is a real model call, so the suite stays small.
- Headless: `claude -p "/gss:spec <slug>" --bare --plugin-dir . --allowedTools ... --output-format json`. Bare mode skips installed plugins, so CI loads the plugin explicitly.
- `claude-code-action@v1` accepts `plugin_marketplaces` and `plugins` inputs, so host repos can run factory stages in Actions without vendoring anything.
- `${CLAUDE_PLUGIN_ROOT}` changes on update; `${CLAUDE_PLUGIN_DATA}` persists. Nothing the factory needs persists outside the host repo, so neither matters much.
- Two things to confirm by trying: whether `"source": "."` in `marketplace.json` works when the marketplace and plugin are the same repo root, and whether a skill with `context: fork` can name a plugin-shipped agent.

## 9. Decisions to confirm

1. **Namespace.** Plugin name `gss`, commands `/gss:factory` and friends. The alternative is a plugin named `factory`, which gives `/factory:build` but an awkward `/factory:factory` for the orchestrator.
2. **Artifact home.** `factory/` at the root of each host repo. The playbook suggests `intent/`; one folder for all stage artifacts seems simpler to find and to index.
3. **Gate mechanism in Iteration 0.** Edit `status: accepted` and commit, rather than a PR per artifact. PR-per-artifact arrives with automation in Iteration 3.
4. **Dogfood first.** The first real work item is the factory itself, and Iteration 0 is built by following the templates by hand.

## 10. Status and next step

Iterations 0, 1 and 2 are built and on `main`. The `factory-conventions` skill holds the current table of which rules are enforced and which stay advisory.

Next: run one real change through `/gss:factory` end to end and record what the skills had to say twice. Then Iteration 3: run stages headlessly in GitHub Actions and sweep factory PRs to green. Iteration 3 needs the `CLAUDE_CODE_OAUTH_TOKEN` repository secret.
