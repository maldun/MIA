"""
tools/smoke_in_stack.sh: runs a smoke check in a throw-away container on the stack's network, where `db` of deploy/.env resolves
(VIEW Deploy finding F-2, the smoke half; SMOKE-TRANSFER-001 was run this way by hand). A stub podman records what it is asked.
Marker: REQ-OPR-001 (the target is checked by one command).   python tests/test_smoke_in_stack.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                          # noqa: E402

URL = "postgresql://mia:secret-pw@db:5432/mia"

# the stub: `network exists` and `image exists` answer from STUB_NETWORK / STUB_IMAGE; `run` writes its arguments, the URL it got
# through the environment and the files of the mounted export, then exits with STUB_RC
STUB = r"""#!/usr/bin/env bash
log="$STUB_LOG"
case "$1 $2" in
  "network exists") [ "$3" = "$STUB_NETWORK" ]; exit $? ;;
  "image exists") [ "$3" = "$STUB_IMAGE" ]; exit $? ;;
esac
if [ "$1" = run ]; then
  printf '%s\n' "$@" > "$log.args"
  printf '%s' "${MIA_DATABASE_URL:-}" > "$log.url"
  prev=""
  for a in "$@"; do
    if [ "$prev" = "-v" ]; then (cd "${a%%:*}" && find . -type f | sort) > "$log.files"; fi
    prev="$a"
  done
  exit "${STUB_RC:-0}"
fi
exit 0
"""


class SmokeInStack(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.podman = os.path.join(self.dir, "podman")
        with open(self.podman, "w") as fp:
            fp.write(STUB)
        os.chmod(self.podman, 0o755)
        self.log = os.path.join(self.dir, "log")
        self.env_file = os.path.join(self.dir, "env")
        with open(self.env_file, "w") as fp:
            fp.write("OLLAMA_URL=http://host.containers.internal:11434\nMIA_DATABASE_URL=%s\n" % URL)

    def run_tool(self, *args, **extra):
        env = {k: v for k, v in os.environ.items() if k not in ("MIA_DATABASE_URL", "MIA_SMOKE_DATABASE_URL", "MIA_IMAGE", "MIA_PROJECT")}
        env.update(PODMAN=self.podman, STUB_LOG=self.log, STUB_NETWORK="mia_default", STUB_IMAGE="localhost/mia:x")
        env.update(extra)
        return subprocess.run(["bash", os.path.join(REPO, "tools", "smoke_in_stack.sh"), *args], capture_output=True, text=True, env=env, cwd=REPO)

    def read(self, suffix):
        with open(self.log + suffix) as fp:
            return fp.read()

    @mark.req("REQ-OPR-001")
    def test_the_smoke_runs_on_the_stack_network_with_the_url_from_the_env_file_and_without_the_env_file(self):
        """Given deploy/.env naming the database `db`, When the tool runs a smoke check, Then podman runs it on mia_default from an export
        without .env files, the URL arrives through the environment only, and the smoke's arguments and exit code pass through"""
        out = self.run_tool("--image", "localhost/mia:x", "--env-file", self.env_file, "tests/smoke/smoke_core_graphs.py", "--database", "mia_smoke", STUB_RC="1")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        args = self.read(".args").split("\n")
        self.assertIn("--network", args)
        self.assertEqual(args[args.index("--network") + 1], "mia_default")
        self.assertIn("localhost/mia:x", args)
        self.assertEqual(args[-4:-1], ["tests/smoke/smoke_core_graphs.py", "--database", "mia_smoke"])
        self.assertEqual(self.read(".url"), URL)
        self.assertNotIn("secret-pw", self.read(".args") + out.stdout + out.stderr)
        files = self.read(".files").split("\n")
        self.assertIn("./tests/smoke/smoke_core_graphs.py", files)
        self.assertFalse([f for f in files if f.endswith("/.env")], "an .env file went into the export")
        self.assertFalse(os.path.exists(args[args.index("-v") + 1].split(":")[0]), "the export was not removed")

    @mark.req("REQ-OPR-001")
    def test_a_missing_network_image_or_script_cannot_run(self):
        """Given no stack network, then no image, then no script, When the tool runs, Then it exits 2 and names what is missing, without podman run"""
        no_net = self.run_tool("--image", "localhost/mia:x", "--env-file", self.env_file, "tests/smoke/smoke_core_graphs.py", STUB_NETWORK="other")
        no_image = self.run_tool("--image", "localhost/mia:y", "--env-file", self.env_file, "tests/smoke/smoke_core_graphs.py")
        no_script = self.run_tool("--image", "localhost/mia:x", "--env-file", self.env_file, "tests/smoke/no_such.py")
        for out, word in ((no_net, "mia_default"), (no_image, "localhost/mia:y"), (no_script, "no_such.py")):
            self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
            self.assertIn(word, out.stdout + out.stderr)
        self.assertFalse(os.path.exists(self.log + ".args"))


if __name__ == "__main__":
    unittest.main()
