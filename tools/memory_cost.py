import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory_records import MemoryRecords, tokens
from storage import Storage
from storage_files import FileBackend

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="memories.json")
    parser.add_argument("--db", default="data/db")
    parser.add_argument("--questions", required=True)
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--budget", type=int, default=400)
    args = parser.parse_args()

    if not os.path.exists(args.history):
        print("no history")
        sys.exit(2)

    try:
        history = json.load(open(args.history))
        if not isinstance(history, list):
            raise ValueError
    except (ValueError, json.JSONDecodeError):
        print("no history")
        sys.exit(2)

    try:
        dreaming_cost = sum(tokens(m["content"]) for m in history)
    except (KeyError, TypeError):
        print("no history")
        sys.exit(2)

    with open(args.questions, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print("no questions")
        sys.exit(2)

    questions = lines[-args.n:]
    storage = Storage(FileBackend(args.db))
    records = MemoryRecords(storage, budget_tokens=args.budget)

    structured_costs = []
    abstained = 0

    for i, q in enumerate(questions):
        found = records.retrieve(q)
        cost = tokens(records.block(found))              # an abstention costs nothing and counts in the mean
        structured_costs.append(cost)
        abstained += 0 if found else 1
        print(f"{i} {cost} tokens, {len(found)} records  {q[:50]}")

    total = len(questions)
    mean = sum(structured_costs) / total

    print(f"dreaming: {dreaming_cost} tokens per answer")
    print(f"structured: mean {mean:.1f} tokens per answer, max {max(structured_costs)}, abstained {abstained} of {total} questions")

    if mean <= dreaming_cost:
        print("not higher than dreaming")
    else:
        print("HIGHER than dreaming")

if __name__ == "__main__":
    main()
