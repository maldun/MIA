"""Amendments A-144 and A-145 of the protected test material (G-V3.PANEL, findings F-08 and F-04 of the first Verify run): TC-WFM-135 (tests/acceptance/test_skill_runs.py) and TC-IF-101-39 say that deleting one history record deletes the run with the id of that record and no other run; the test adapter delete_history gets the run id (tests/helpers/contract.py, the IF-101 mock); new TC-IF-101-40: another account gets 404 for a run and never sees it as shown (the mock now checks the account). Built in a sandbox copy: on the old tree the new tests fail (TC-WFM-135, TC-IF-101-39 mock and real, TC-IF-101-40 mock), with the patch the 8 tests of test_skill_runs and the 78 of test_if_101_chat_api pass (2 skips, as before). The code fix of `_history_changed` (T-11) is in skill_runs.py and comes after the install.
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
