"""Amendment of the protected helper tests/helpers/contract.py for IF-201 v3 on the real chat agent (G-V3.CHAT T-02): the adapter of IF-201 takes the mock option `phases`, gives the
ChatService a digest step on a scripted model (it repeats the first 300 characters of the user text) and the declared phases, and gets the operation `skill_turn`. Without it the real variants
of TC-IF-201-09, -10, -11 and -12 cannot run. The patch was built and run in a sandbox copy: all 100 tests of test_if_201_chat_turn and test_if_101_chat_api pass (2 skips, as before).
usage: python3 -I specs/mia/goals/G-V3/contract-change-4/install.py [--do]   (any directory; without --do it only checks that the patch applies)"""
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
