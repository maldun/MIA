"""/search: the top results of the search tool as a chat message, no model, no answer."""
try:
    from ... import constants as CONST
    from ... import research_chat
except ImportError:  # used as plain script / in tests
    import constants as CONST
    import research_chat


def make(services):
    def run(query, on_delta, on_emotion, should_stop, run_report=None):
        text = research_chat.run_search(services.web_search(), query, count=services.cfg.get(CONST.SEARCH_RESULTS_SHOWN_KEY, CONST.DEFAULT_SEARCH_RESULTS_SHOWN), should_stop=should_stop)
        if run_report is not None and text:
            run_report(text)      # the text is escaped Markdown already (format_results); the runtime's own report would escape it a second time
        return text
    return run
