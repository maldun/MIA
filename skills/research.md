---
name: research
version: 1
description: "answer a question from the web with quotes (the baseline without a strategy; strategies are pinned by a variant)"
model: {profile: light}
pipeline: research.baseline@1
tools: [web_search, fetch_page]
budget: {steps: 30, seconds: 300, search_calls: 6, fetch_calls: 12}
max_safety: {reads_web: true}
status_block: true
---
