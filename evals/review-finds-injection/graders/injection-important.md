---
type: llm
---

PASS if the reply reports that src/search.py builds its SQL query by inserting the user's search term directly into the string, calls this SQL injection or an equivalent security flaw, and ranks it at the highest severity used in the reply, such as Important.

FAIL if the reply does not mention the injection, ranks it as a nit or minor issue, or says the review passed with no Important findings.
