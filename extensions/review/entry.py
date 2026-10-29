"""/review question [until DATE]: the literature review (review_chat.py). The skills run through the core, the questions to the user through the chat (ask), the figures to the status card
(monitor), the report as a record and as files (reports, files). The questions and a short result are spoken, never the whole report."""
try:
    from ... import research_chat, review_chat
except ImportError:  # used as plain script / in tests
    import research_chat
    import review_chat


def make(services):
    def run(text, on_delta, on_emotion, should_stop, ask=None, options=None, monitor=None, files=None, reports=None):
        def run_skill(name, inputs):
            result = services.core.run(name, inputs, should_stop=should_stop)
            if result.status == "stopped":
                raise RuntimeError("the review was stopped")
            if result.status != "done":
                raise RuntimeError(research_chat.friendly_error(result.error))
            return result.answer
        return review_chat.run_review(text, run_skill, services.scholar, services.review_full_text, ask, on_event=services.pipeline_event, should_stop=should_stop, cfg=services.cfg,
                                      speak=services.speaker("review"), options=options, monitor=monitor, files=files, reports=reports)
    return run
