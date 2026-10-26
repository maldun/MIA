"""Turn the plausibility proposal into the plausibility record, in the name of the person who rates (L2b).

Usage: python3 -I tools/apply_plausibility.py <repository root> --by "<name>" [--date YYYY-MM-DD] [--accept-unflagged]
  --accept-unflagged   the person accepts the proposal for every item that is NOT flagged `attention` (basis text and rating as proposed)
Flagged items are written only when the person has filled `decision` and `basis` (and `probe` or `accepted_risk` for questionable) in the proposal;
the others stay without a record and the check names them. The script rates nothing by itself: without --by it refuses to run."""
import argparse
import datetime
import pathlib

import yaml

HARDWARE = "Fedora, Ryzen 9 5900X (12 cores), 62 GB RAM, RX 7800 XT with 16 GB, podman, models through Ollama (num_ctx 8192)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--by", required=True)
    ap.add_argument("--date", default=str(datetime.date.today()))
    ap.add_argument("--accept-unflagged", action="store_true")
    args = ap.parse_args()
    root = pathlib.Path(args.root)
    proposal = yaml.safe_load((root / "specs/mia/plausibility-proposal.yaml").read_text(encoding="utf-8"))["proposal"]
    decisions_file = root / "specs/mia/plausibility-decisions.yaml"
    if decisions_file.exists():                   # the person's decisions from plausibility-review.md win over the proposal
        for iid, decided in (yaml.safe_load(decisions_file.read_text(encoding="utf-8")) or {}).get("decisions", {}).items():
            proposal.setdefault(iid, {}).update(decided)
    items, open_items = {}, []
    for iid, p in proposal.items():
        if p.get("decision"):                         # decided by the person (the categories multi-user and field are the owner's decisions)
            item = {"rating": p["decision"], "basis": p.get("basis") or []}
            for key in ("probe", "accepted_risk", "method", "claims", "note"):
                if p.get(key):
                    item[key] = p[key]
        elif p.get("attention") or not args.accept_unflagged:
            open_items.append(iid)
            continue
        else:
            item = {"rating": p["proposed"], "basis": [p["basis"]] if isinstance(p["basis"], str) else p["basis"]}
        item.update(rated_by=args.by, rated=args.date, hardware="HW-target")
        items[iid] = item
    record = {"plausibility": {"hardware": {"HW-target": HARDWARE}, "references": {}, "items": items}}
    (root / "specs/mia/plausibility.yaml").write_text("# Plausibility record (L2b). Written by tools/apply_plausibility.py from plausibility-proposal.yaml, rated by %s.\n" % args.by
                                                      + yaml.safe_dump(record, sort_keys=True, allow_unicode=True).replace("{by}", args.by).replace("{date}", args.date), encoding="utf-8")
    print("%d rated, %d without a record yet" % (len(items), len(open_items)))


main()
