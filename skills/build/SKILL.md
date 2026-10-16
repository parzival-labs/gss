---
name: build
description: Build stage of the GSS Factory. Implements an accepted factory/<slug>/plan.md step by step on branch factory/<slug>, running the project's checks after each step and keeping plan.md in sync. Use for /gss:build.
argument-hint: <slug>
---

# /gss:build

Read the `factory-conventions` skill. Input is an accepted `factory/<slug>/plan.md`. Output is commits on branch `factory/<slug>` and a `build:` line in `log.md`.

## Steps

1. Refuse to start if `plan.md` is missing or still `draft`, or if its Checks section is empty.
2. Check out branch `factory/<slug>`. Run the checks once before changing anything and record the baseline. If they fail on a clean branch, stop and report; that is not this work item's problem to hide.
3. For each step in Order of work:
   - Implement only that step.
   - Run the checks. Paste the final lines of output into your working notes, not a summary.
   - If green, commit with the step number and title as the message.
   - If red, fix within the step. Do not edit a test to make it pass unless the plan's Tests section says that test changes in this step. This rule is advisory in Iteration 0; a hook enforces it from Iteration 2.
4. If reality diverges from the plan, edit `plan.md` in the same commit as the code change and say why in the commit body. The plan stays `accepted`; the divergence is visible in the diff.
5. When all steps are done, run the full checks one final time. Append to `log.md`:

   ```
   <date> build: checks passed (<summary of output>) at <short sha>
   ```

   or `build: checks failed` with the failing output, and stop without shipping.
6. Commit the log line. Stop with: "Build complete on `factory/<slug>`. Run `/gss:factory <slug>` to ship."

Done means the checks ran in this session and passed, and their output is in the log. Not "should pass".
