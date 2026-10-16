---
name: review
description: Review stage of the GSS Factory. Runs the reviewer subagent in a fresh context over a built work item's diff, writes factory/<slug>/review.md with ranked findings, and routes back to build when Important findings are open. Use for /gss:review or "review the <slug> work item".
argument-hint: <slug>
---

# /gss:review

Read the `factory-conventions` skill. Input is a `build: checks passed` line in `factory/<slug>/log.md` that is newer than any `review:` line. Output is `factory/<slug>/review.md` and a `review:` line in `log.md`.

## Steps

1. Refuse to start if the newest `build:` line is missing or says failed.
2. Delegate the review to the `reviewer` subagent from this plugin. Give it only the slug and the default branch name. Do not pass it your own opinion of the change, a summary of what you built, or what you expect it to find; a reviewer handed a conclusion tends to confirm it.
3. If the reviewer cannot be spawned, stop and say so. Do not review the change yourself: the session that built it may not approve it.
4. Write `factory/<slug>/review.md` from `templates/review.md`. Copy the reviewer's findings table verbatim. Set `important_open` in the frontmatter to the number of Important findings. Leave every Disposition as `open`.
5. Append to `log.md`:

   ```
   <date> review: <n> important, <m> nits at <short sha>
   ```

6. Commit as `Review <slug>`.
7. Stop with one of:
   - Important findings open: "Review found <n> Important findings in `factory/<slug>/review.md`. Run `/gss:factory <slug>` to fix them in the build stage." The next build fixes them and a fresh review runs after.
   - None open: "Review passed with <m> nits. Run `/gss:factory <slug>` to ship." Nits ride along as a list in the PR body; they do not block.

The human gate after review is the pull request itself. Review findings never approve or block on their own.
