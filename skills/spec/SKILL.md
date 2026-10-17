---
name: spec
description: Spec stage of the GSS Factory. Turns an accepted factory/<slug>/intent.md into spec.md with requirements, constraints applied and concerns flagged, then stops for acceptance. Use for /gss:spec.
argument-hint: <slug>
---

# /gss:spec

Read the `factory-conventions` skill. Input is an accepted `factory/<slug>/intent.md`. Output is `factory/<slug>/spec.md` from `templates/spec.md`.

## Steps

1. Refuse to start if `intent.md` is missing or still `draft`. Say which gate is open.
2. Read `intent.md`, the project's `CLAUDE.md`, and any project skill that describes a policy or convention. These are the constraints.
3. Delegate codebase exploration to the `researcher` subagent from this plugin, giving it the slug and `intent.md`. Use its touch points, conventions and surprises as input. If it cannot be spawned, explore read-only yourself.
4. Write the Concerns flagged section first. A concern is anything where the intent conflicts with a constraint, existing behaviour, or itself. Name the owner who can resolve each one. If there are none, say "none" and why you are confident.
5. Write numbered, testable requirements. Each traces to the intent's proposed outcome. If a requirement cannot be made testable, it is an open question, not a requirement.
6. Write acceptance criteria concrete enough for the reviewer agent to check later.
7. Write `spec.md` with `status: draft`, append `spec: drafted` to `log.md`, commit as `Draft spec for <slug>`.
8. Stop with the gate message. If concerns were flagged, say so in the message: the product owner should resolve them before accepting.

Scope rule: the spec may narrow the intent, with the narrowing listed under Out of scope. It may not widen it. New ideas go in a new intent.
