---
name: research
version: 3
description: "answer a question from the web with quotes (the cheap try first, decomposition only when it finds nothing; other pipelines are pinned by a variant)"
model: {profile: light}
pipeline: research.escalate@1
tools: [web_search, fetch_page]
budget: {steps: 150, seconds: 600, search_calls: 12, fetch_calls: 30}
max_safety: {reads_web: true}
status_block: true
---
