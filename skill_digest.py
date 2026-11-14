"""
The digest step of the Chat agent (REQ-CHA-048 to 054, 061 to 063, G-V3.CHAT): words the status messages, the end summary, the failure and the stop message of a
skill run in MIA's persona, reading a long result in pieces. Interface note: specs/mia/goals/G-V3.CHAT/digest-step-interface.md.
STUB of Plan Step 4: the constructor exists; the attributes `tools` and `prompt` are missing on purpose; the four methods raise NotImplementedError until Implement writes them.
"""


class SkillDigestStep:
    # Implement adds the attributes `tools` (an empty tuple, REQ-CHA-048) and `prompt` (it names 1200 characters, REQ-CHA-052); they are left out here so that their checks are red

    def __init__(self, model, persona="", input_tokens=4096, count_tokens=None):
        self._model, self._persona, self._input_tokens = model, persona, input_tokens
        self._count = count_tokens or (lambda text: max(1, len(text) // 4))

    def status(self, phase):
        raise NotImplementedError("REQ-CHA-041")

    def failure(self, reason):
        raise NotImplementedError("REQ-CHA-044")

    def stopped(self, reason):
        raise NotImplementedError("REQ-CHA-057")

    def summary(self, full_result):
        raise NotImplementedError("REQ-CHA-043, 050, 051, 062, 063")
