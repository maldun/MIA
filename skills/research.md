---
name: research
version: 2
description: "answer a question from the web with quotes (the baseline without a strategy; strategies are pinned by a variant)"
model: {profile: light}
pipeline: research.baseline@1
tools: [web_search, fetch_page]
budget: {steps: 150, seconds: 600, search_calls: 12, fetch_calls: 30}
max_safety: {reads_web: true}
status_block: true
---
