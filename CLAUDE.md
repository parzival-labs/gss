# GSS

Gregarious Simulation Systems. This repo builds the GSS Factory, an agentic
software factory for Claude Code, and distributes it as a plugin.

## Layout

- `docs/DESIGN.md`: the design proposal. Read it before changing anything else.
- `.github/workflows/`: Claude code review and `@claude` mention workflows.
- `REVIEW.md`: review-only rules for the managed Code Review service.
- Plugin files arrive with Iteration 0: `.claude-plugin/`, `skills/`, `agents/`, `hooks/`, `evals/`.

## Conventions

- Plain markdown everywhere. Keep docs and skills short enough to read in one sitting.
- No third-party dependencies in plugin scripts. Python 3 standard library only.
- Every rule in a skill is advisory until a hook or CI check enforces it. Say which it is.
- Claims about how Claude Code behaves must come from code.claude.com/docs, with the page named.

## Checks

Until Iteration 1 there is no test suite. Before a PR, confirm:

- `claude plugin validate .` passes once `.claude-plugin/plugin.json` exists.
- Workflow YAML parses.

## Code review

These rules apply to any Claude review of a PR here, in CI or locally.

Important means one of:

- A statement about Claude Code plugin, skill, hook or action mechanics that contradicts the current docs.
- A workflow or hook change that could block legitimate work, leak a secret, or widen permissions.
- A skill or agent instruction that contradicts `docs/DESIGN.md` without updating it.

Everything else is Nit at most: wording, structure, markdown style. Report at most five Nits per review.
Do not report formatting or link style. Do not review `*.lock` files.
