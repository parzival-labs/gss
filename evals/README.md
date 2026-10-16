# GSS Factory evals

Run from the repo root:

```
claude plugin eval . --scaffold --trust-plugin
```

`--scaffold` is needed because cases build their fixture repositories with the `fixture.sh` script beside them. The scripts only write files and git state into the run's empty workspace. Every run is a real model call on your account.

Cheaper while iterating: add `--runs 1 --ablation none`.

| Case | What it protects |
|---|---|
| intent-asks-questions | Intent stage questions the originator instead of jumping to a solution |
| factory-waits-at-gate | Orchestrator stops at a draft artifact instead of running the next stage |
| spec-refuses-draft-intent | Spec stage will not start before the intent is accepted |
| build-refuses-without-checks | Build stage will not start with no check commands |
| review-finds-injection | Review stage delegates to the reviewer agent, which ranks a SQL injection as Important |

Rule from the playbook: every escaped defect in a factory-built change becomes a new case here.
