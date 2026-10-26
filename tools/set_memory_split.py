"""
Set the split field for each case in the memory sample file.

Usage:
python3 tools/set_memory_split.py
python3 tools/set_memory_split.py --do
"""

import argparse
import json
import sys
from collections import defaultdict


PATH = "specs/mia/eval-drafts/memory_sample.jsonl"
HOLDOUT = [
    "MEM-S04",
    "MEM-S09",
    "MEM-S10",
    "MEM-S13",
    "MEM-S16",
    "MEM-S18",
    "MEM-S20",
    "MEM-S22",
    "MEM-S25",
    "MEM-S27",
]


def set_memory_split():
    cases = []
    with open(PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))

    case_ids = {case["id"] for case in cases}
    for id in HOLDOUT:
        if id not in case_ids:
            print(f"unknown id in HOLDOUT: {id}")
            sys.exit(2)

    new_cases = []
    changes = []
    dev_count = 0
    holdout_count = 0
    category_counts = defaultdict(lambda: {"dev": 0, "holdout": 0})

    for case in cases:
        if case.get("label") is None:                  # not labelled by the owner yet: no split either
            new_cases.append(case)
            continue
        old_split = case.get("split", "none")
        new_split = "holdout" if case["id"] in HOLDOUT else "dev"

        if old_split != new_split:
            changes.append(
                f"{case['id']} category={case.get('category', 'unknown')}: {old_split} -> {new_split}"
            )

        if new_split == "dev":
            dev_count += 1
        else:
            holdout_count += 1

        category = case.get("category", "unknown")
        category_counts[category][new_split] += 1

        new_case = {}                                  # every other field stays; "split" goes right after "label"
        for key, value in case.items():
            if key == "split":
                continue
            new_case[key] = value
            if key == "label":
                new_case["split"] = new_split
        new_case.setdefault("split", new_split)
        new_cases.append(new_case)

    for change in changes:
        print(change)

    print(f"dev: {dev_count}, holdout: {holdout_count}")
    for category in sorted(category_counts.keys()):
        counts = category_counts[category]
        print(f"{category} dev: {counts['dev']}, holdout: {counts['holdout']}")

    parser = argparse.ArgumentParser(description="Set the split field for each case.")
    parser.add_argument("--do", action="store_true", help="Write the changes to the file.")
    args = parser.parse_args()

    if args.do:
        with open(PATH, "w", encoding="utf-8") as f:
            for case in new_cases:
                f.write(json.dumps(case, ensure_ascii=False) + "\n")
        print("written")
    else:
        print("nothing written (use --do)")


if __name__ == "__main__":
    set_memory_split()
