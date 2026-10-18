---
name: verify_computable
version: 1
description: "check a computable claim (a model-written script recomputes it from the data in the sandbox)"
triggers: ["recompute", "check the calculation", "is this number right"]
model: {profile: light}
pipeline: verify.computable
tools: []
budget: {steps: 14, seconds: 240}
max_safety: {runs_code: true}
status_block: true
variant: default
---
## lines
### write
- Drafting a little experiment…
- Scribbling a check…
### run
- Running the experiment in the sandbox…
- Putting the claim to the test…
