---
name: summarize
version: 1
description: summarize a text in a few sentences with the key points
triggers: ["summarize", "tl;dr", "short version"]
model: {profile: light}
pipeline: summarize
tools: []
budget: {steps: 6, seconds: 300}
status_block: true
variant: default
---
## prompts
### system
You summarize texts faithfully. You never add facts that are not in the text.
### summarize
Summarize the following text in at most {{input.sentences}} sentences, in the language of the text, and list up to 5 key points.

Text:
{{input.text}}
## schemas
### summary
```json
{"type": "object", "required": ["summary", "key_points"],
 "properties": {"summary": {"type": "string", "minLength": 1, "maxLength": 1500},
                "key_points": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 300}}}}
```
## lines
### summarize
- Condensing the essence…
- Boiling it down…
