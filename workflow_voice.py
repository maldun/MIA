"""
Who speaks (owner 2026-10-29): every task that has something to say (/lookup, /review, the workflows to come) asks here whether its voice is on, so there is one rule and not one option per workflow.

  workflow_speak          general switch of setup_cfg.json, default true
  workflow_speak_tasks    optional {task: true | false} over it, for the one task that should differ (for example {"review": false})

A value that is not a boolean is ignored. The chat answers themselves are not governed by this (the voice of the chat is the product); it is for the tasks that run beside it.
"""


def speaker_for(cfg, task, speak):
    """`speak` if the voice is on for `task`, else None (a task with no voice says nothing and still gives its text)"""
    cfg = cfg or {}
    per_task = (cfg.get("workflow_speak_tasks") or {}).get(task)
    general = cfg.get("workflow_speak", True)
    on = per_task if isinstance(per_task, bool) else (general if isinstance(general, bool) else True)
    return speak if on else None
