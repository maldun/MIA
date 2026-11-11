"""The toolbox of the Workflow management (N-2.3, G-V2.TOOLBOX T-01 to T-05): STUB, written in Plan step 4 so the red tests import.

Real behaviour comes with plan tasks T-01 to T-05 (REQ-WFM-050..056, 067, 068, 070, 090..095). The tests in tests/acceptance/test_toolbox.py fix this interface:
- Toolbox(library, is_owner, events): `library` is the part `transforms` of IF-203 v1 (mock: tests/helpers/mocks/if_203_transforms.py), `is_owner(account)` says whether an
  account is the owner (REQ-WFM-066), `events.record(event)` takes the event of REQ-WFM-093 (stand-in for IF-401).
- import_transform(text, author) -> the transform ID; the exchange form is one JSON text with id, version, inputs, outputs and code (a field `status` in it is ignored);
  a text that fails the check raises ToolboxError("invalid_file") naming the first problem; an ID that exists with an equal or lower version raises ToolboxError("duplicate_id")
  naming the ID; a higher version replaces the code and keeps trust and lifecycle (REQ-WFM-092); the code text is never compiled or run here.
- export_transform(id) -> the exchange text; a shipped transform raises ToolboxError("not_exportable"), why names "no code text".
- look_up(id) -> {"id", "version", "trust", "lifecycle", "reason", "evidence", "baseline_allowed", "shipped"}; `reason` says why a transform is untrusted.
- offer() -> the sorted IDs a new graph may pick (retired ones left out).
- set_trust(id, value, account), set_lifecycle(id, value, account, evidence=None, allow_baseline=False): a value outside the lists raises ToolboxError("invalid_trust" or
  "invalid_lifecycle"); trusted by an account that is not the owner, and allow_baseline by one, raise ToolboxError("owner_only"); `tested` without evidence raises
  ToolboxError("evidence_missing"). The status stays as it was when an error is raised.
- run(id, args, as_baseline=False) -> the result of the code text's run(args); an untrusted transform raises ToolboxError("untrusted") unless it runs as the baseline of a check
  with the owner's allowance; a retired one raises ToolboxError("retired") unless as_baseline.
- seed_shipped(nodes_dir): every ID of nodes_dir/<id>/<version>.json once, in its highest version that is not retired, trusted and shipped, without a code text.
ToolboxError has `code` and `why` (a text for the person).
"""


class ToolboxError(Exception):
    def __init__(self, code, why=""):
        super().__init__("%s: %s" % (code, why))
        self.code, self.why = code, why


class Toolbox:
    def __init__(self, library, is_owner, events):
        self.library, self.is_owner, self.events = library, is_owner, events

    def import_transform(self, text, author):
        return None

    def export_transform(self, tid):
        return "{}"

    def look_up(self, tid):
        return {"id": tid, "version": 0, "trust": None, "lifecycle": None, "reason": None, "evidence": None, "baseline_allowed": False, "shipped": False}

    def offer(self):
        return []

    def set_trust(self, tid, value, account):
        return None

    def set_lifecycle(self, tid, value, account, evidence=None, allow_baseline=False):
        return None

    def run(self, tid, args, as_baseline=False):
        return None

    def seed_shipped(self, nodes_dir):
        return None
