# Review instructions

Read with the Code review section of `CLAUDE.md`, which holds the shared rules.

## What Important means here

This is a markdown-first repository: design docs, skills, agent definitions,
hooks and GitHub workflows. Reserve Important for findings that would make the
factory misbehave or mislead a reader about Claude Code: wrong claims about
plugin, skill, hook or action mechanics; a hook or workflow that could block
legitimate work, leak a secret or widen permissions; a skill that contradicts
`docs/DESIGN.md`. Wording and structure are Nit at most.

## Cap the nits

Report at most five Nits per review.

## Do not report

- Markdown formatting, heading levels, link style
- `*.lock` files
- Anything a future CI check already enforces, once `claude plugin validate` runs in CI

## Always check

- A new or changed skill says which of its rules are advisory and which are enforced by a hook
- A new hook script explains in its block message why it blocked and how to get approval
- A workflow change keeps the minimum `permissions:` block it needs
