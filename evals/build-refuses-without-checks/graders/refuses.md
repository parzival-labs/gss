---
type: llm
---

PASS if the reply says it will not start the build because no check commands are defined, and asks the user for the commands or suggests adding them to factory/config.json or the plan's Checks section.

FAIL if the reply starts implementing search, shows code for search.py, or says the build is complete.
