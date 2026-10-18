---
name: extract_claims
version: 1
description: "find the checkable claims in a text (a model reads it, code keeps only what is really in the text)"
model: {profile: light}
pipeline: extract.llm@1
tools: []
budget: {steps: 6, seconds: 120}
status_block: false
---
