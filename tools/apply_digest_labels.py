"""Applies the marks that the form of make_digest_label_form.py downloaded to eval/labels/<suite>.jsonl (G-V3.CHAT T-04). Only the owner runs it: the labels are truth set by a person.
usage: python3 -I tools/apply_digest_labels.py MARKS.json SUITE --by NAME [--labels-dir eval/labels] [--do]   (without --do it only shows what would be appended)
A mark that repeats a label already in the file with the same values is skipped; a changed value is appended and overrides the earlier line (the scorer reads later lines last)."""
import json
import os
import sys
from datetime import date

FIELDS = ("faithful", "persona", "resisted")


def load(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def new_lines(marks, existing, by, today):
    """the label lines to append: marks with at least one boolean field, not already in the file with the same values"""
    current = {}
    for item in existing:
        current.setdefault((item["case"], item["output_sha1"]), {}).update({k: item[k] for k in FIELDS if k in item})
    lines = []
    for mark in marks:
        values = {k: mark[k] for k in FIELDS if isinstance(mark.get(k), bool)}
        if not values or not mark.get("case") or not mark.get("output_sha1"):
            continue
        known = current.get((mark["case"], mark["output_sha1"]), {})
        if all(known.get(k) == v for k, v in values.items()):
            continue
        lines.append(dict({"case": mark["case"], "output_sha1": mark["output_sha1"]}, **values, note=mark.get("note", ""), by=by, date=today))
    return lines


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i] in ("--by", "--labels-dir")}
    if len(args) - len(opts) != 2 or "--by" not in opts:
        sys.exit(__doc__)
    marks_path, suite = [a for a in args if a not in opts.values()]
    path = os.path.join(opts.get("--labels-dir", "eval/labels"), suite + ".jsonl")
    with open(marks_path, encoding="utf-8") as fp:
        lines = new_lines(json.load(fp), load(path), opts["--by"], date.today().isoformat())
    print("%d label lines to append to %s" % (len(lines), path))
    for item in lines:
        print(" ", item["case"], item["output_sha1"][:8], {k: item[k] for k in FIELDS if k in item})
    if "--do" in argv and lines:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fp:
            fp.writelines(json.dumps(item, ensure_ascii=False) + "\n" for item in lines)
        print("appended")
    elif lines:
        print("dry run; add --do to append")


if __name__ == "__main__":
    main(sys.argv[1:])
