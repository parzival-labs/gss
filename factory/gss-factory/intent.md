---
stage: intent
status: draft
accepted_by:
accepted_at:
ticket:
---

# Intent: GSS Factory

## Problem

Building software with Claude Code is fast at the coding step and slow everywhere else. Each unit of work needs the same scaffolding by hand: writing down what is wanted, turning that into requirements, planning before editing, verifying before declaring done, and getting a reviewable PR. Nothing enforces the order, so steps get skipped under time pressure, and the record of who asked for what and who accepted it lives in chat history instead of git.

## Proposed outcome

A contributor types one slash command with an idea and is walked around the loop from Anthropic's AI-native SDLC playbook: intent, spec, plan, build, ship. Each stage leaves a markdown artifact in the repo that a human accepts before the next stage runs. The same command resumes a work item from wherever it stopped. The factory is installed into any project as a Claude Code plugin from this repo.

## Affected users and systems

- Engineers and product owners using Claude Code in projects that install the plugin.
- This repository, which holds the plugin and is the first project to use it.
- GitHub, where pull requests are the final gate and Claude code review runs.

## Constraints

- Plain markdown and standard-library Python only. No build step, no package installs in host projects.
- No state outside git. Artifacts under `factory/<slug>/` in the host repo are the only record.
- Humans own the gates. The factory never accepts its own artifacts or approves its own PRs.
- Follow the documented Claude Code plugin mechanics. Where the platform cannot enforce a rule, say so and plan a hook.

## Out of scope

- Replacing trackers such as Jira or Linear. A ticket ID in the frontmatter is the only link.
- Multi-repo work items.
- Production deployment and the Maintain stage, until the build loop is solid.

## Open questions

- Should low-risk work items be allowed to skip the plan gate, and who decides the risk tier?
- When a stage runs headlessly in CI, who is recorded as the accepting human?
