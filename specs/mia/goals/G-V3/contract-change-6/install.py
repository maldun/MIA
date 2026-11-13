"""Renumbering of G-V3 against master (owner decision 2026-11-13: master keeps its numbers): D-304 to D-309 become D-332 to D-337 and the amendment A-143 (elements in the run record) becomes A-149, in the protected files that name them: contracts/IF-101-chat-api.md, contracts/IF-302-record-tables.md, specs/mia/plausibility.yaml and the docstring of tests/acceptance/test_skill_run_observer.py. Text only, no code and no assertion changes. All other files were renamed in the commit before this payload.
usage: python3 -I specs/mia/goals/G-V3/contract-change-6/install.py [--do]   (any directory; without --do it only checks that the patch applies)"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
do = "--do" in sys.argv
check = subprocess.run(["git", "-C", str(ROOT), "apply", "--check", "-p1", str(HERE / "contract.patch")], capture_output=True, text=True)
print(check.stdout.strip() or check.stderr.strip() or "the patch applies")
if check.returncode:
    sys.exit("the patch does not apply (already installed or the file changed)")
if do:
    subprocess.run(["git", "-C", str(ROOT), "apply", "-p1", str(HERE / "contract.patch")], check=True)
    print("installed")
else:
    print("dry run; add --do to install")
