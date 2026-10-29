"""/search: the top results of the search tool as a chat message, no model, no answer."""
try:
    from ... import constants as CONST
    from ... import research_chat
except ImportError:  # used as plain script / in tests
    import constants as CONST
    import research_chat


def make(services):
    def run(query, on_delta, on_emotion, should_stop):
        return research_chat.run_search(services.web_search(), query, count=services.cfg.get(CONST.SEARCH_RESULTS_SHOWN_KEY, CONST.DEFAULT_SEARCH_RESULTS_SHOWN), should_stop=should_stop)
    return run
