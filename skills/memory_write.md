---
name: memory_write
version: 3
description: "decide what to remember from one message of the user (facts, preferences, commitments); code stores it and refuses any other source"
model: {profile: light}
pipeline: memory.write@3
tools: []
budget: {steps: 2, seconds: 30}
status_block: false
---
