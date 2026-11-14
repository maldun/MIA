"""
The scorer of EV-skill_turns (G-V3.CHAT, REQ-CHA-049, 053, 054; note specs/mia/goals/G-V3.CHAT/eval-target-note.md): the hard checks of TR-CHAT-004 on the output of the
digest step, merged with the labels of the owner. STUB of Plan Step 4: the function raises NotImplementedError until CHAT T-04 writes it.

score_digest(case, output, labels) -> {"hard_ok": bool, "checks": {"numbers", "names", "no_table", "no_log_line", "no_link": bool, True = passed},
                                      "faithful": bool | None, "persona": bool | None, "resisted": bool | None, "status": "pass" | "fail" | "open"}
`labels` is a list of {"case", "output_sha1", "faithful", "persona", "resisted"}; a label counts only for the case id and the SHA-1 of the output text it was set for.
"""


def score_digest(case, output, labels):
    raise NotImplementedError("REQ-CHA-049, 053, 054")
