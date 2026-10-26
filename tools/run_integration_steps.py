"""Run every integration step (tests/integration/<node>/step_NN/): Python steps one by one, JavaScript steps with node --test.

Usage: python3 -I tools/run_integration_steps.py [repository root]   (exit 1 if a step fails; skipped steps are not failures)
unittest discover does not walk into the step folders (they are not packages), so the stage uses this runner."""
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
failed = 0
steps = sorted((root / "tests/integration").glob("*/step_*/test_step.py"))
for step in steps:
    out = subprocess.run([sys.executable, str(step)], capture_output=True, text=True, cwd=root)
    last = (out.stderr.strip().splitlines() or ["?"])[-1]
    print("%-45s %s" % (step.relative_to(root / "tests/integration").parent, last))
    if out.returncode:
        failed += 1
        print(out.stderr[-1200:])
js = sorted((root / "tests/integration").glob("*/step_*/test_step.test.mjs"))
if js:
    out = subprocess.run(["node", "--test"] + [str(f) for f in js], capture_output=True, text=True, cwd=root)
    print("\n".join(l for l in out.stdout.splitlines() if l.startswith("# ") and any(w in l for w in ("tests", "pass", "fail", "skipped"))))
    if out.returncode:
        failed += 1
        print(out.stdout[-1500:])
print("%d python steps, %d javascript steps, %d failed" % (len(steps), len(js), failed))
sys.exit(1 if failed else 0)
