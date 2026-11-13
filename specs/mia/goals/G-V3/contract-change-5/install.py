"""Amendment of the protected test tests/acceptance/test_skill_runs.py for A-144 (G-V3.PANEL, finding F-08 of the first Verify run): TC-WFM-135 says that deleting one history record deletes the run with the id of that record and no other run; the test of the whole account is replaced. The new test is red against the recorder of 92075cb and green after the T-11 fix of `_history_changed`.
usage: python3 -I specs/mia/goals/G-V3/contract-change-5/install.py [--do]   (any directory; without --do it only checks that the patch applies)"""
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
