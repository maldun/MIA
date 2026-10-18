---
name: verify_claim
version: 1
description: "judge a claim that no hard check can decide (one voice; the other verification styles are pinned by a variant: verify.consistency, verify.jury, verify.cops, verify.trial)"
model: {profile: light}
pipeline: verify.single@1
tools: []
budget: {steps: 12, seconds: 300}
status_block: false
---
