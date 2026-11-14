"""Installs the contract change of G-V3 (A-140, A-141, A-142; D-302, D-303) into the repository: the mocks and the contract suites (protected, so the
owner runs this), and the contracts IF-101 v16, IF-201 v3, IF-302 v8, IF-102 v4. The files in `payload/` were built and run in a sandbox:
all mock variants of the four suites pass, and the real variants fail only in the new or changed tests (red first, until the code follows).
usage: python3 -I specs/mia/goals/G-V3/contract-change/install.py [--do]   (any directory; without --do it only lists what would change)"""
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
