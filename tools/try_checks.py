"""
Tries the hard checks on example claims (or your own), without MIA: the library picks the checks that fit each claim, the result and the trace are printed.
The web checks (citation, web confirmation) use the real search and fetch tools with their safety rules and need --web.

Run with the MIA virtualenv from the MIA folder:
  python tools/try_checks.py                          the built-in examples without web access
  python tools/try_checks.py --web                    also citation and web confirmation (needs internet; SearXNG if it runs, else DuckDuckGo)
  python tools/try_checks.py --claim '{"type": "numeric", "data": {"expression": "12*1.5+3", "value": 21}}'
  python tools/try_checks.py --list                   which checks the library has for which claim types

A claim is {"type": quotation | citation | numeric | unit | date | structured | schedule | fact, "text": "...", "data": {fields of the checks}}.
"""
import argparse
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)
from MIA.config import default_path as default_config  # noqa: E402

from MIA import checks, web_tools  # noqa: E402
from MIA.core import Core  # noqa: E402
from MIA.library import Library  # noqa: E402
from MIA.pipeline import Tool  # noqa: E402

SOURCE = "The Eiffel Tower is 330 metres tall, including its antennas. It was completed in 1889 for the World's Fair in Paris."
EXAMPLES = [
    ("a quote that is in the source", {"type": "quotation", "data": {"quote": "330 metres tall", "source": SOURCE}}),
    ("a quote that is not", {"type": "quotation", "data": {"quote": "the tower is 12 metres tall and green", "source": SOURCE}}),
    ("a near match", {"type": "quotation", "data": {"quote": "The Eiffel Tower is 300 metres tall, including its antennas.", "source": SOURCE}}),
    ("arithmetic", {"type": "numeric", "data": {"expression": "12*1.5+3", "value": 21}}),
    ("wrong arithmetic", {"type": "numeric", "data": {"expression": "12*1.5+3", "value": 22}}),
    ("units", {"type": "unit", "data": {"value": 330, "from_unit": "m", "to_unit": "ft", "result_value": 1083}}),
    ("a wrong weekday", {"type": "date", "data": {"kind": "weekday", "date": "1889-03-31", "weekday": "Monday"}}),
    ("an overlap in a schedule", {"type": "schedule", "data": {"events": [{"name": "talk", "start": "09:00", "end": "10:30"}, {"name": "lunch", "start": "10:00", "end": "11:00"}]}}),
]
WEB_EXAMPLES = [
    ("a real citation", {"type": "citation", "data": {"url": "https://en.wikipedia.org/wiki/Eiffel_Tower", "quote": "Eiffel Tower"}}),
    ("a page that does not exist", {"type": "citation", "data": {"url": "https://en.wikipedia.org/wiki/This_page_does_not_exist_12345", "quote": "anything at all"}}),
    ("a local address", {"type": "citation", "data": {"url": "http://127.0.0.1:8585/api/presets", "quote": "anything at all"}}),
    ("a fact on the web", {"type": "fact", "text": "The Eiffel Tower was completed in 1889", "data": {"entities": ["Eiffel Tower", "1889"], "facts": ["1889"]}}),
]


def show(label, claim, outcome):
    print("\n== %s: %s -> %s (%s)" % (label, claim["type"], outcome["verdict"], outcome["status"]))
    for step in outcome["trace"]:
        print("   %-26s %s" % (step["ref"], step.get("status", "skipped: " + step.get("skipped", "")) + ("  " + step["detail"] if step.get("detail") else "")))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cfg", default=default_config(REPO))
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--claim", action="append", default=[], help="a claim as JSON")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    with open(args.cfg) as fp:
        cfg = json.load(fp)
    work = tempfile.mkdtemp()
    library = Library(os.path.join(REPO, "library"))
    tools, _, _ = web_tools.build_web_tools(cfg, work)
    core = Core(os.path.join(REPO, "skills"), library, work, tools={n: Tool(*pair) for n, pair in tools.items()},
                functions=checks.build_web_checks(tools["web_search"][0], tools["fetch_page"][0]))
    if args.list:
        for entry in library.entries("node"):
            if "check" in entry["tags"] and entry.get("applies_to", {}).get("claim_types"):
                print("%-28s %-22s %s%s" % (entry["id"], ",".join(entry["applies_to"]["claim_types"]), entry["title"], "  [web]" if entry["safety"]["reads_web"] else ""))
        return
    claims = [("your claim", json.loads(c)) for c in args.claim] or EXAMPLES + (WEB_EXAMPLES if args.web else [])
    for label, claim in claims:
        show(label, claim, core.checks.run(claim, include_web=args.web))
    print("\nweb log (what was asked of the internet): %s" % work)


if __name__ == "__main__":
    main()
