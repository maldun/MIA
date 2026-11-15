"""Installs the red acceptance tests of G-V3 (Plan Step 4) into the repository; the owner runs it (tests/acceptance is protected).
usage: python3 -I specs/mia/goals/G-V3/red-tests/install.py [--do]   (without --do it only lists what would change)"""
import filecmp
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PAYLOAD = HERE / "payload"
do = "--do" in sys.argv
for src in sorted(p for p in PAYLOAD.rglob("*") if p.is_file()):
    rel = src.relative_to(PAYLOAD)
    dst = ROOT / rel
    state = "new" if not dst.exists() else ("same" if filecmp.cmp(src, dst, shallow=False) else "changed")
    print("%-8s %s" % (state, rel))
    if do and state != "same":
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
print("installed" if do else "dry run; add --do to install")
