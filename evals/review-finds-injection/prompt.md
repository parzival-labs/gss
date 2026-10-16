---
description: The review stage delegates to the reviewer subagent, which flags a SQL injection against an explicit spec requirement as Important.
tags: [review]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

/gss:review add-search
