---
name: ship
description: Ship stage of the GSS Factory. Pushes branch factory/<slug> and opens a draft pull request whose body links the work item's artifacts and quotes the check output. Use for /gss:ship.
argument-hint: <slug>
---

# /gss:ship

Read the `factory-conventions` skill. Input is a `build: checks passed` line in `factory/<slug>/log.md`. Output is a draft pull request and a `ship:` line.

## Steps

1. Refuse to start if the last `build:` line in `log.md` is missing or says failed.
2. Push `factory/<slug>` to the remote with upstream tracking.
3. Open a draft pull request against the default branch, using whatever GitHub tooling the session has: the `gh` CLI or a GitHub tool. If neither is available, print the title and body and ask the user to open it.
4. Title: the intent's title. Body, in this order:
   - One paragraph: the problem and the outcome, from `intent.md`.
   - Links to `intent.md`, `spec.md` and `plan.md` on the branch.
   - The acceptance criteria from `spec.md` as a checklist.
   - The final check output from `log.md`, in a code block.
   - Any Open questions still carried.
5. Append `<date> ship: draft PR #<n>` to `log.md`, commit, push.
6. Stop with the PR link and: "The merge is the final gate. Review intent and risk, not every line."

The session that built the code does not approve it. From Iteration 1 the reviewer agent reviews before this stage; until then, PR review happens on GitHub.
