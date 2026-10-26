---
name: memory_write
version: 6
description: "decide what to remember from one message of the user (facts, preferences, commitments); code stores it and refuses any other source"
model: {profile: light, options: {temperature: 0.2}}
pipeline: memory.write@5
tools: []
budget: {steps: 2, seconds: 30}
status_block: false
---
