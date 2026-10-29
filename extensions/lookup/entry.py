"""/lookup (the old /research): the skill `research` searches, reads and answers with quotes; the steps go to the status block of the answer, the answer to the chat."""
try:
    from ... import constants as CONST
    from ... import research_chat
except ImportError:  # used as plain script / in tests
    import constants as CONST
    import research_chat


def make(services):
    def run(question, on_delta, on_emotion, should_stop):
        return research_chat.run_research(services.core, question, pipeline=services.cfg.get(CONST.RESEARCH_PIPELINE_KEY, CONST.DEFAULT_RESEARCH_PIPELINE),
                                          on_event=services.pipeline_event, should_stop=should_stop, speak=services.speaker("lookup"),
                                          on_sources=services.note_sources, trust=services.trust_for_url())      # a fresh table: the trust of sources is edited on the page
    return run
