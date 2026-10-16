---
name: intent
description: Intent stage of the GSS Factory. Turns a plain-language idea into factory/<slug>/intent.md by asking analyst-style questions, then stops for acceptance. Use for "capture this as an intent" or /gss:intent.
argument-hint: <idea>
---

# /gss:intent

Read the `factory-conventions` skill. The output is `factory/<slug>/intent.md` from `templates/intent.md`.

## Steps

1. If no idea was given, ask for one sentence describing the problem.
2. Ask the analyst questions, all at once, at most five, and only the ones the idea does not already answer:
   - Who has this problem, and how do they notice it today?
   - What would be true once it is solved?
   - Which systems or parts of the codebase are involved?
   - What must not change?
   - How will we know it worked?
3. Do not propose a solution. If the user offers one, record it under Proposed outcome as "the originator suggests", and keep the outcome itself solution-neutral.
4. Create branch `factory/<slug>` from the default branch if it does not exist. Fill the template. Keep every section. Put anything you had to guess under Open questions rather than inventing an answer.
5. Write `intent.md` with `status: draft`, append `intent: drafted` to `log.md`, commit as `Draft intent for <slug>`.
6. Stop with the gate message.

Done when the originator could hand `intent.md` to someone who was not in the conversation and that person would understand the problem and the desired outcome.
