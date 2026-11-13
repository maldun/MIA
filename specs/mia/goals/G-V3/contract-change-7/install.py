"""Comments only in tests/acceptance/contract/test_if_101_chat_api.py: the Given / When / Then markers of the two tests TC-IF-101-39 and TC-IF-101-40 that contract-change-5 installed (test_doc_check rule T3: the new tests had none, so the count of errors rose by one against the tag). No code line, no assertion and no name changes; the 78 tests give the same result with and without the patch.
usage: python3 -I specs/mia/goals/G-V3/contract-change-7/install.py [--do]   (any directory; without --do it only checks that the patch applies)"""
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
