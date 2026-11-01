"""Compose stack (N-4.2 T-03): TC-OPR-007 (REQ-OPR-007, the files), TC-OPR-008 (REQ-OPR-008), TC-OPR-010 (REQ-OPR-010). Run with: python tests/test_compose_stack.py"""
import os
import re
import sys
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                         # noqa: E402

DEPLOY = os.path.join(REPO, "deploy")
VARIANTS = ("compose.yaml", "compose.rocm.yaml", "compose.nvidia.yaml")
FUNNEL_CALL = re.compile(r"""tailscale\s+funnel|["']funnel["']""")


def load(name):
    """the services of one compose file, as written"""
    with open(os.path.join(DEPLOY, name), encoding="utf-8") as fp:
        return yaml.safe_load(fp)["services"]


def published(name):
    """(service, port line) for every published port of one compose file, as written"""
    with open(os.path.join(DEPLOY, name), encoding="utf-8") as fp:
        services = yaml.safe_load(fp)["services"]
    return [(service, str(line)) for service, spec in services.items() for line in (spec or {}).get("ports", [])]


def scripts():
    """paths of the shell and Python files of the repository outside tests/, specs/ and hidden folders"""
    found = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("tests", "specs", "node_modules", "__pycache__")]
        found += [os.path.join(root, f) for f in files if f.endswith((".sh", ".py"))]
    return found


class ComposeStack(unittest.TestCase):

    @mark.req('REQ-OPR-008')
    def test_only_the_https_front_publishes_a_port_off_loopback(self):
        """TC-OPR-008: every published port of a service other than https is bound to 127.0.0.1, whatever .env says.

        Example: mia "127.0.0.1:${MIA_PORT:-8585}:8585" -> loopback; "${MIA_BIND:-127.0.0.1}:8585:8585" -> refused, MIA_BIND may be 0.0.0.0.
        """
        # Given: the published ports of every compose variant
        for name in VARIANTS:
            for service, line in published(name):
                # When: the service is not the HTTPS front
                if service == "https":
                    continue
                # Then: the port line starts with the loopback address itself, not a variable
                self.assertTrue(line.startswith("127.0.0.1:"), "%s: %s publishes %s" % (name, service, line))

    @mark.req('REQ-OPR-008')
    def test_the_https_front_is_published_and_mia_has_its_loopback_port(self):
        """TC-OPR-008: the stack still publishes the https front and the local http page of mia (A-37).

        Example: compose.yaml -> https publishes 8586, mia publishes 127.0.0.1:8585.
        """
        # Given: the ports of the base compose file
        ports = published("compose.yaml")
        # When: they are grouped by service
        services = [service for service, line in ports]
        # Then: https and mia each publish exactly one port
        self.assertEqual(services.count("https"), 1)
        self.assertEqual(services.count("mia"), 1)

    @mark.req('REQ-OPR-008')
    def test_no_script_uses_tailscale_funnel(self):
        """TC-OPR-008: no shell or Python script runs tailscale funnel (public); a comment that warns against it is fine.

        Example: tailscale_serve.py calls "serve" -> fine; a line 'tailscale funnel 443' or the argument "funnel" -> refused.
        """
        # Given: every script of the repository
        offenders = []
        for path in scripts():
            with open(path, encoding="utf-8", errors="replace") as fp:
                for number, text in enumerate(fp, 1):
                    # When: the line is code, not a comment or the backticked warning of a docstring
                    code = text.split("#", 1)[0].replace("`tailscale funnel`", "")
                    if FUNNEL_CALL.search(code):
                        offenders.append("%s:%d" % (os.path.relpath(path, REPO), number))
        # Then: none calls funnel
        self.assertEqual(offenders, [])

    @mark.req('REQ-OPR-007')
    def test_the_graph_app_has_its_own_container_from_the_mia_image(self):
        """TC-OPR-007: the graph app (N-5) runs in its own service built from the mia image, with no published port (D-133).

        Example: services.graph.image == localhost/mia:latest, no ports, its command serves graph_app.
        """
        # Given: the services of the base file
        services = load("compose.yaml")
        # When: the graph service is read
        graph = services.get("graph") or {}
        # Then: the mia image, no port of its own, a command that serves graph_app
        self.assertEqual(graph.get("image"), services["mia"]["image"])
        self.assertNotIn("ports", graph)
        self.assertIn("graph_app", " ".join(graph.get("command") or []))

    @mark.req('REQ-OPR-007')
    def test_the_https_front_routes_graph_to_the_graph_container(self):
        """TC-OPR-007: the https front sends /graph/ to the graph service and everything else to mia (D-133).

        Example: Caddyfile has handle_path /graph/* { reverse_proxy graph:8587 } and reverse_proxy mia:8585.
        """
        # Given: the Caddyfile of the https front
        with open(os.path.join(DEPLOY, "Caddyfile"), encoding="utf-8") as fp:
            caddyfile = fp.read()
        # When: its routes are read
        graph_route = re.search(r"handle_path\s+/graph/\*\s*\{\s*reverse_proxy\s+graph:(\d+)", caddyfile)
        # Then: /graph/ goes to graph on the port its command serves, the rest to mia
        self.assertIsNotNone(graph_route)
        self.assertIn(graph_route.group(1), load("compose.yaml")["graph"]["command"])
        self.assertIn("reverse_proxy mia:8585", caddyfile)

    @mark.req('REQ-OPR-010')
    def test_the_model_server_loads_one_model_in_every_variant(self):
        """TC-OPR-010: OLLAMA_MAX_LOADED_MODELS is 1 for CPU, ROCm and NVIDIA (an overlay adds to the base environment).

        Example: compose.yaml "1", compose.rocm.yaml without it -> "1".
        """
        # Given: the environment of ollama in the base file
        base = dict(load("compose.yaml")["ollama"]["environment"])
        for name in VARIANTS:
            # When: the variant's overlay is merged over it
            environment = dict(base)
            environment.update((load(name).get("ollama") or {}).get("environment") or {})
            # Then: one model at a time
            self.assertEqual(str(environment["OLLAMA_MAX_LOADED_MODELS"]), "1", name)


if __name__ == "__main__":
    unittest.main()
