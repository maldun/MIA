#!/usr/bin/env bash
# A test budget for the review: only 3 works are screened instead of 40 (the run mode stops at limit x cap_factor = 3 x 1 = 3 and asks "continue / summarize / stop"). Idempotent.
# It writes `review_budget` into setup_cfg.local.json (the settings of this machine, laid over setup_cfg.json key by key, not in git); the live setup_cfg.json is not touched, so "off" only
# removes that key again (the file is deleted when nothing else is in it). The app reads the setup at its start: restart it after on and after off.
#   bash tools/review_test_budget.sh on       3 works screened (keeps the other values of review_budget of setup_cfg.json, e.g. seconds)
#   bash tools/review_test_budget.sh off      back to the budget of setup_cfg.json
#   bash tools/review_test_budget.sh status   what is set now
# In the chat start the test review with the factor 1, else the hard cap is 3 x 10 = 30 works:   /review options cap_factor=1 -- <your question>
set -eu
cd "$(dirname "$0")/.."
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
"$PY" -I - "${1:-status}" <<'PY'
import json
import os
import sys

action = sys.argv[1]
base, local = "setup_cfg.json", "setup_cfg.local.json"
if action not in ("on", "off", "status"):
    sys.exit("usage: review_test_budget.sh on|off|status")
with open(base, encoding="utf-8") as fp:
    budget = dict(json.load(fp).get("review_budget") or {})
extra = {}
if os.path.exists(local):
    with open(local, encoding="utf-8") as fp:
        extra = json.load(fp)
    if not isinstance(extra, dict):
        sys.exit("%s must be a json object" % local)
if action == "status":
    print("review_budget of %s: %s" % (base, budget))
    print("review_budget of %s: %s" % (local, extra.get("review_budget", "not set")))
    print("test budget is %s" % ("ON (screen %s)" % extra["review_budget"].get("screen") if "review_budget" in extra else "off"))
elif action == "on":
    extra["review_budget"] = {**budget, "screen": 3}
    with open(local, "w", encoding="utf-8") as fp:
        json.dump(extra, fp, indent=2)
        fp.write("\n")
    print("ON: review_budget = %s in %s; restart the app, then /review options cap_factor=1 -- <question>" % (extra["review_budget"], local))
else:
    if "review_budget" not in extra:
        print("already off (nothing in %s)" % local)
    else:
        del extra["review_budget"]
        if extra:
            with open(local, "w", encoding="utf-8") as fp:
                json.dump(extra, fp, indent=2)
                fp.write("\n")
        else:
            os.remove(local)
        print("OFF: back to review_budget of %s = %s; restart the app" % (base, budget))
PY
