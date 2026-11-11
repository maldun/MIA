"""Amendment of the protected helper tests/helpers/contract.py for IF-101 v16/v17 on the real backend (G-V3.PANEL T-05): the scripted review of the real adapter declares two phases
(asking, reporting) and reports them through the monitor, and the adapter gets shown_run, skill_run and delete_history. Without it TC-IF-101-34, -35, -36, -38 and -39 skip or fail on the real
provider. The patch was built and run in a sandbox copy: all 76 tests of test_if_101_chat_api pass (2 skips, as before).
usage: python3 -I specs/mia/goals/G-V3/contract-change-3/install.py [--do]   (any directory; without --do it only checks that the patch applies)"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
do = "--do" in sys.argv
check = subprocess.run(["patch", "-p1", "--dry-run", "-d", str(ROOT), "-i", str(HERE / "contract.patch")], capture_output=True, text=True)
print(check.stdout.strip() or check.stderr.strip())
if check.returncode:
    sys.exit("the patch does not apply (already installed or the file changed)")
if do:
    subprocess.run(["patch", "-p1", "-d", str(ROOT), "-i", str(HERE / "contract.patch")], check=True)
    print("installed")
else:
    print("dry run; add --do to install")
