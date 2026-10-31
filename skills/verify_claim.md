---
name: verify_claim
version: 2
description: "judge a claim: the number gate checks the numbers by code first, then cops judges a claim with a number and evidence, one voice a claim without a number; a number without evidence abstains (v2, D-153; the styles verify.single, verify.consistency, verify.jury, verify.cops, verify.trial are pinned by a variant)"
model: {profile: light}
pipeline: verify.number_gate@5
tools: []
budget: {steps: 12, seconds: 300}
status_block: false
---
