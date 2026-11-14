"""Re-applies the CURRENT rules of option1b.py to the proposals stored in a run (accepted and refused, no model, no GPU).
usage: python3 -I revalidate_option1b.py RUN_DIR DOCS_DIR OUT_DIR [max_ungrounded=0]
Used after the fix of rule 1 (headings glued to a sentence): the refused proposals of the first run keep their text, so the run
need not be repeated. Chunk failures are kept as they were."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import option1b
from checks import norm

run, docs, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 0
out.mkdir(parents=True, exist_ok=True)
for f in sorted(run.glob("*.json")):
    r = json.loads(f.read_text())
    text = (docs / f"{f.stem}.txt").read_text()
    props = [dict(a) for a in r["accepted"]] + [x["item"] for x in r["refused"] if "kind" in x["item"]]
    failed = [x for x in r["refused"] if "kind" not in x["item"]]
    acc, ref = [], list(failed)
    for p in props:
        why = option1b.validate(p, text, limit)
        (ref.append(dict(item=p, reason=why)) if why else acc.append(p))
    (out / f.name).write_text(json.dumps(dict(accepted=acc, refused=ref, chunks=r["chunks"], seconds=r.get("seconds")), indent=1))
    print(f.stem, len(r["accepted"]), "->", len(acc), "accepted;", len(r["refused"]), "->", len(ref), "refused")
