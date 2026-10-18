---
stage: intent
status: draft
accepted_by:
accepted_at:
ticket:
---

# Intent: Parzival Labs brain

## Problem

Parzival Labs is a one- or two-person AI product company building several products of different types, all hosted in GitHub. GSS today is a per-repo factory: it works only where its Claude Code plugin loads. Cloud sessions in the Claude app (mobile and web) do not load repo-enabled plugins, and the account is Claude Max, so org managed settings are not available as a way to push the plugin everywhere. The originator works from a phone a lot.

Status is scattered. In the originator's words: "Today I have to keep an eye on the status in the Claude app if I worked on them there - if I just worked in the CLI I have to remember what is happening in everything in GitHub." There is no single place that shows what is in flight, what finished and what is waiting on the originator, across all products and across the agent harnesses that did the work (Claude Code locally, Claude Code in the cloud, Pi, Codex). Nobody can see what a run cost either.

## Proposed outcome

GSS is the control plane ("brain") for Parzival Labs. Once this is done:

- From a phone or any other device, behind a simple protected web interface, the originator can see every product's in-progress work items, what finished, and what is waiting on them (a question or an approval). Visibility comes first and does not depend on which harness did the work.
- Work runs both autonomously in the cloud and interactively with a person at a laptop, through the same stages and gates.
- The originator can set a cost limit and see cost per run and in total, per project.
- Low-risk changes, such as dependency updates, can merge without a human once tests pass and enough observability is in place (the originator's view, answer 3; the definition of "low risk" and "enough observability" is open).
- The originator is not tied to GitHub, to one agent harness, or to one model vendor, even though every product is on GitHub today.

Principles already agreed in discussion, recorded here as constraints on any solution:

- Git in each repo stays the source of truth. The brain only indexes it.
- Enforcement is checked by a runner outside the agent, so it survives a change of harness.
- Standards are written once in neutral markdown, with thin per-harness shims.
- Visibility before autonomy.
- The brain stays thin and is pulled by real products, never built ahead of them.
- Docs cite the source (Anthropic playbook, Brickbank, Spotify) for each borrowed idea.

The originator suggests (a solution, not a requirement): a front end and orchestrator on Cloudflare, using Workers, Workflows for durable gates, and a Durable Object or D1 product registry. It knows every product and its repo, accepts requests or ticket references, and runs the agent headless in a Cloudflare Sandbox container. The orchestrator holds the credentials, and egress is limited to the model gateway and the git host. The originator sees this as mirroring two setups:

- The Brickbank team's Tina/Buck/Vera: orchestrator on AWS Lambda durable functions, Pi agent in Bedrock AgentCore, evidence checked in code, humans asked only for a question or an approval.
- Spotify's Xirp/Portal: harness-neutral sessions, with session metadata flowing back to one place so anyone can see what is done and where to resume.

These descriptions are the originator's account. The spec stage must check them against the sources before they are cited in docs.

## Affected users and systems

- Users: the originator and, possibly, one other person at Parzival Labs. They view status, answer questions, approve gates and set cost limits.
- GSS plugin: skills, agents, hooks, `bin/`, and the artifacts under `factory/<slug>/` need to work outside Claude Code, or gain neutral equivalents.
- Every Parzival Labs product repo on GitHub: each gains the factory artifacts and some way of reporting status.
- New, if the suggested solution is taken: a Cloudflare account, a registry of products, a web interface with authentication, a headless agent runner, and credential and egress handling.
- `docs/DESIGN.md` lists multi-repo orchestration and production deployment as non-goals. This work item changes that, so the design doc must be updated with it.

## Constraints

- Claude Max account: no org managed settings. Cloudflare's documented route uses API billing, not the Max subscription, so model spend is a real cost and must be visible and limitable.
- The status interface must be usable on a phone and protected, not public.
- Repo conventions apply: plain markdown, plugin scripts use the Python 3 standard library only, and every rule says whether it is advisory or enforced. Claims about Claude Code behaviour come from code.claude.com/docs, with the page named.
- Small changes must not carry heavy process overhead.
- Known risks: building the factory instead of products; vendors shipping the same features; process overhead for small changes; model spend.

## Out of scope

- Building any capability ahead of a real product that needs it.
- Replacing git as the source of truth, or replacing GitHub, Jira, Linear or other trackers. Not being tied to GitHub means not designing it out, not migrating off it.
- Choosing or building a replacement for any particular model vendor or harness.
- Decisions about the products themselves.

## Open questions

- What is "low risk" and "enough observability" for auto-merge? The originator had no detailed view. It also conflicts with the current design, where a human merge is the final gate, so `docs/DESIGN.md` needs a decision.
- What is the smallest first slice? Visibility seems to come first. Does it need the Cloudflare orchestrator at all, or could status be read from the git host and from session reports?
- How does status get from each harness to the brain, including the Claude app's cloud sessions, which do not load the plugin? What do the cloud sessions do load?
- Which cost figures are available per harness, and how is a per-run limit enforced, not only reported?
- How many products and people at the start, and which product pulls the first slice?
- Authentication for the web interface: who can see it, and is one other person ever an approver?
- Whether the suggested Cloudflare design is the right one is for the spec stage to weigh against alternatives.
