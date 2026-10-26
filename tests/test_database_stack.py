"""The database container and its place in the compose stack (N-3.1 T-08): TC-SLY-010 and TC-SLY-011, plus the checks of the compose file that need no container.
The container tests need podman, podman-compose and the image postgres:16; they are skipped, never weakened, where one is missing.
Run with: python tests/test_database_stack.py"""
import os
import shutil
import socket
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEPLOY = os.path.join(ROOT, "deploy")
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

IMAGE = "docker.io/library/postgres:16"
PROJECT = "mia-test-db-%d" % os.getpid()
ALONE = "mia-test-db-alone-%d" % os.getpid()


def sh(*args, env=None, cwd=None):
    return subprocess.run(list(args), capture_output=True, text=True, cwd=cwd, env=dict(os.environ, **(env or {})))


class ComposeFile(unittest.TestCase):
    """No container needed: the shape of the service."""

    @classmethod
    def setUpClass(cls):
        try:
            import yaml
        except ImportError:
            raise unittest.SkipTest("PyYAML is not installed")
        with open(os.path.join(DEPLOY, "compose.yaml"), encoding="utf-8") as handle:
            cls.compose = yaml.safe_load(handle)

    @mark.req("REQ-SLY-010")
    def test_the_database_publishes_no_port_and_starts_only_with_its_profile(self):
        db = self.compose["services"]["db"]
        self.assertNotIn("ports", db)
        self.assertEqual(db["profiles"], ["db"])
        self.assertEqual(db["image"], IMAGE)

    @mark.req("REQ-SLY-011")
    def test_health_check_volume_and_schema_at_the_first_start(self):
        db = self.compose["services"]["db"]
        self.assertIn("pg_isready", " ".join(db["healthcheck"]["test"]))
        self.assertIn("pgdata:/var/lib/postgresql/data", db["volumes"])
        self.assertTrue(any(v.startswith("./db:/docker-entrypoint-initdb.d") for v in db["volumes"]))
        self.assertIn("pgdata", self.compose["volumes"])
        self.assertTrue(os.path.exists(os.path.join(DEPLOY, "db", "001_records.sql")))

    @mark.req("REQ-SLY-011")
    def test_the_stack_without_the_profile_is_unchanged_and_the_password_is_not_in_the_file(self):
        self.assertTrue({"mia", "https", "ollama", "searxng"} <= set(self.compose["services"]))
        with open(os.path.join(DEPLOY, "compose.yaml"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("${POSTGRES_PASSWORD:-}", text)
        self.assertEqual(sh("bash", "-n", os.path.join(DEPLOY, "up.sh")).returncode, 0)


def need_podman():
    if shutil.which("podman") is None or shutil.which("podman-compose") is None:
        raise unittest.SkipTest("podman or podman-compose is not available")
    if sh("podman", "image", "exists", IMAGE).returncode != 0 and sh("podman", "pull", "-q", IMAGE).returncode != 0:
        raise unittest.SkipTest("the image %s cannot be pulled" % IMAGE)


def wait_ready(container, seconds=60):
    for _ in range(seconds * 2):
        if sh("podman", "exec", container, "pg_isready", "-U", "mia", "-d", "mia").returncode == 0:
            time.sleep(1)                         # the image restarts once after its init scripts
            if sh("podman", "exec", container, "pg_isready", "-U", "mia", "-d", "mia").returncode == 0:
                return True
        time.sleep(0.5)
    return False


def tables(container):
    out = sh("podman", "exec", container, "psql", "-U", "mia", "-d", "mia", "-tAc", "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1")
    return out.stdout.split()


class DatabaseContainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        need_podman()
        env = {"SEARXNG_SECRET": "test", "POSTGRES_PASSWORD": "test", "COMPOSE_PROJECT_NAME": PROJECT}
        cls.addClassCleanup(lambda: sh("podman-compose", "-p", PROJECT, "-f", "compose.yaml", "--profile", "db", "down", "-v", env=env, cwd=DEPLOY))
        cls.addClassCleanup(lambda: sh("podman", "rm", "-f", ALONE))
        up = sh("podman-compose", "-p", PROJECT, "-f", "compose.yaml", "--profile", "db", "up", "-d", "db", env=env, cwd=DEPLOY)
        if up.returncode != 0:
            raise unittest.SkipTest("the stack does not start: " + (up.stderr or up.stdout)[-200:])
        cls.stack = PROJECT + "_db_1"
        if not wait_ready(cls.stack):
            raise unittest.SkipTest("the database of the stack is not ready in 60 s")
        cls.ip = sh("podman", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", cls.stack).stdout.strip()

    @mark.req("REQ-SLY-010")
    def test_refused_from_the_host_the_lan_and_a_container_outside_the_stack_but_open_inside(self):
        """TC-SLY-010: no published port; the host address and the address of the home network are refused; a container on another network gets no answer;
        a container of the stack connects by the service name."""
        self.assertEqual(sh("podman", "port", self.stack).stdout.strip(), "")
        lan = [a for a in sh("hostname", "-I").stdout.split() if ":" not in a][:1]
        for address in ["127.0.0.1"] + lan + [self.ip]:
            with self.subTest(address=address), self.assertRaises(OSError):
                socket.create_connection((address, 5432), timeout=2).close()
        outside = sh("podman", "run", "--rm", IMAGE, "pg_isready", "-h", self.ip, "-p", "5432", "-t", "3")
        self.assertNotEqual(outside.returncode, 0, outside.stdout)
        inside = sh("podman", "run", "--rm", "--network", PROJECT + "_default", "-e", "PGPASSWORD=test", IMAGE, "psql", "-h", "db", "-U", "mia", "-d", "mia", "-tAc", "SELECT 1")
        self.assertEqual(inside.stdout.strip(), "1", inside.stderr)

    @mark.req("REQ-SLY-011")
    def test_the_same_tables_alone_and_in_the_stack_and_the_container_is_healthy(self):
        """TC-SLY-011: started alone with the same settings, then by the stack: ready both times, the same tables."""
        run = sh("podman", "run", "-d", "--name", ALONE, "-e", "POSTGRES_USER=mia", "-e", "POSTGRES_DB=mia", "-e", "POSTGRES_PASSWORD=test",
                 "-v", os.path.join(DEPLOY, "db") + ":/docker-entrypoint-initdb.d:ro,z", "--tmpfs", "/var/lib/postgresql/data", IMAGE)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(wait_ready(ALONE))
        self.assertEqual(tables(ALONE), tables(self.stack))
        self.assertEqual(tables(self.stack), ["records", "schema_version"])
        self.assertEqual(sh("podman", "healthcheck", "run", self.stack).returncode, 0)


if __name__ == "__main__":
    unittest.main()
