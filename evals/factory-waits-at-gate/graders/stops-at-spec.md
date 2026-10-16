---
type: llm
---

PASS if the reply says the work item is waiting for spec.md to be accepted and tells the user how to accept it, for example by setting status to accepted and committing, then running the command again.

FAIL if the reply starts or presents a plan, lists implementation steps, writes code, or says it has accepted the spec itself.
