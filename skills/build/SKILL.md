---
name: build
description: Build stage of the GSS Factory. Implements an accepted factory/<slug>/plan.md step by step on branch factory/<slug>, running the project's checks after each step and keeping plan.md in sync. Use for /gss:build.
argument-hint: <slug>
---

# /gss:build

Read the `factory-conventions` skill. Input is an accepted `factory/<slug>/plan.md`. Output is commits on branch `factory/<slug>` and a `build:` line in `log.md`.

## Steps

1. Refuse to start if `plan.md` is missing or still `draft`, or if there are no checks: neither `factory/config.json` has a `checks` array nor `plan.md` has a Checks section with commands.
   - **Fix mode.** If `review.md` exists with `important_open` above 0, this run fixes those findings instead of starting the plan from the top. Treat each open Important finding as a step. After fixing one, set its Disposition to `fixed in <sha>`. Then continue from step 5.
2. Check out branch `factory/<slug>`. Run the checks once before changing anything and record the baseline. If they fail on a clean branch, stop and report; that is not this work item's problem to hide.
3. For each step in Order of work:
   - Implement only that step.
   - Run the checks. Paste the final lines of output into your working notes, not a summary.
   - If green, commit with the step number and title as the message.
   - If red, fix within the step. Do not edit a test to make it pass unless the plan's Tests section says that test changes in this step. Enforced: the `guard_edits` hook blocks edits to tests that exist on the default branch unless plan.md names them. If a test genuinely must change, add it to plan.md's Tests section in the same commit and say why.
4. If reality diverges from the plan, edit `plan.md` in the same commit as the code change and say why in the commit body. The plan stays `accepted`; the divergence is visible in the diff.
5. When all steps are done and checks are green, run the `simplifier` subagent once on the slug. If it changed anything, run the checks, and commit its edits as their own step titled `Simplify`; if checks fail, revert its edits rather than fix them. Then delegate the final check to the `verifier` subagent from this plugin, giving it only the slug. It runs the checks in a fresh context and returns literal output. Do not run the final check yourself and report it as the verifier's; if the verifier cannot be spawned, run the checks yourself and say so in the log line. Append to `log.md`:

   ```
   <date> build: checks passed (<summary of output>) at <short sha>
   ```

   or `build: checks failed` with the failing output, and stop without shipping.
6. Commit the log line. Stop with: "Build complete on `factory/<slug>`. Run `/gss:factory <slug>` to review."

Done means the verifier ran the checks in this session and they passed, and the verdict is in the log. Not "should pass". Enforced: the `done_means_checked` Stop hook will not let the session end quietly while code is newer than the last passing `build:` line.
