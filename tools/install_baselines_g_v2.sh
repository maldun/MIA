#!/usr/bin/env bash
# Owner step of G-V2 (D-355): the five baselines of the old runner for the equivalence criteria of AC-34.
# Copies data/eval/<suite>__<variant>__20261115-*.jsonl (runs of the old runner, 3 repeats, pin MP-light) to eval/baselines/<suite>__<variant>__baseline.jsonl.
# Before it shows, per run: the pin, the repeats and whether the suite files are the ones of today (suite_sha1 in the header). A run of an older suite is marked STALE: do not install it.
# usage: bash tools/install_baselines_g_v2.sh [--do]   (run it in the main checkout, where data/eval/ is)
set -u
cd "$(dirname "$0")/.." || exit 1
. tools/amendment_lib.sh; amendment_args "$@"
PY=${MIA_PY:-/home/maldun/prog/Python/venvs/mia312/bin/python}
stale=0
for pair in research:escalate plans:free verdicts:single computable:computable2 extraction:llm; do
    suite=${pair%%:*}; variant=${pair##*:}
    src=$(ls -t data/eval/${suite}__${variant}__20261115-*.jsonl 2>/dev/null | head -1)
    if [ -z "$src" ]; then echo "MISSING run: data/eval/${suite}__${variant}__20261115-*.jsonl"; stale=1; continue; fi
    "$PY" -I - "$src" "$suite" <<'PYEOF' || stale=1
import hashlib, json, os, subprocess, sys
src, suite = sys.argv[1:3]
head = json.loads(open(src, encoding="utf-8").readline())
pin = head.get("pin", {})
verdict = []
for name, old in sorted(head["suite_sha1"].items()):
    path = "eval/suites/%s/%s" % (suite, name)
    cur = open(path, "rb").read()
    if hashlib.sha1(cur).hexdigest() == old:
        verdict.append("%s same" % name); continue
    found = None                                    # the version the run used, from git: only the tags of the cases (A-120, split:dev) may differ
    for c in subprocess.check_output(["git", "log", "--format=%h", "--", path], text=True).split():
        b = subprocess.check_output(["git", "show", c + ":" + path])
        if hashlib.sha1(b).hexdigest() == old:
            found = b; break
    plain = lambda bs: [{k: v for k, v in json.loads(l).items() if k != "tags"} for l in bs.decode().splitlines() if l.strip()]
    if found is not None and name.endswith(".jsonl") and plain(found) == plain(cur):
        verdict.append("%s only tags differ" % name)
    else:
        verdict.append("%s STALE (content changed or old version not in git)" % name)
print("%s: pin %s %s, repeats %s, cases %s; %s" % (os.path.basename(src), pin.get("id"), (pin.get("digest") or "")[:19], head["repeats"], head["cases"], ", ".join(verdict)))
sys.exit(1 if any("STALE" in v for v in verdict) else 0)
PYEOF
    copy "$src" "eval/baselines/${suite}__${variant}__baseline.jsonl"
done
[ "$stale" = 1 ] && echo "!! at least one run is missing or stale: do not use --do before this is clear"
finish
