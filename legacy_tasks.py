"""
Bridge for the old way of giving ChatService its tasks (`run_lookup=`, `run_search=`, `run_review=`): builds the Tasks the skills describe themselves. To be removed when the tests that pass these
arguments pass a registry (REQ-WFM-029: the core names no skill). New skills never come here: they register a Task.
"""
try:
    from .research_chat import lookup_task, search_task
    from .review_chat import review_task
except ImportError:  # used as plain script / in tests
    from research_chat import lookup_task, search_task
    from review_chat import review_task


def tasks(run_lookup=None, run_search=None, run_review=None):
    found = []
    if run_lookup is not None:
        found.append(lookup_task(run_lookup))
    if run_search is not None:
        found.append(search_task(run_search))
    if run_review is not None:
        task = review_task(run_review)
        task.needs = ("ask",)                 # the old function takes only the question and the way to ask; options and monitor come with the new run function (web_app)
        found.append(task)
    return found
