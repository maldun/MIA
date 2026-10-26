"""The persona for the model (REQ-CHA-008): the shared persona file (data/persona.json, edited on the page, IF-101 persona) becomes the system message of every call.
The text is used as it was saved; the default form of address is master, unless the persona says otherwise. The old calibration.txt stays as a fallback for a setup
that has no persona file yet. Whether the model then behaves as the persona says is measured with the check dialogues (AC-8), not here."""
import json

ADDRESS_RULE = "Address every user as master, unless the persona above says otherwise."
ADDRESS_ALONE = "Address every user as master."


def read_persona(path):
    """the `text` of the persona file, or "" for a missing, broken or textless file (no persona is not an error)"""
    try:
        with open(path, encoding="utf-8") as fp:
            text = json.load(fp).get("text")
    except (OSError, ValueError, AttributeError):
        return ""
    return text if isinstance(text, str) else ""


def persona_block(text, fallback=""):
    """the system message: the persona (else the fallback text) and the default address; the default alone when there is neither"""
    chosen = text if (text or "").strip() else fallback
    if not (chosen or "").strip():
        return ADDRESS_ALONE
    return "%s\n\n%s" % (chosen.rstrip("\n"), ADDRESS_RULE)
