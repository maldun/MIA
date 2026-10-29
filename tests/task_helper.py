"""Helper of the tests that need a ChatService with tasks: builds a registry from the manifests of the real extensions (extensions/<id>/manifest.json) with run functions of the test
instead of the entries. `prefix` is "MIA." for tests that import the package through a link (so that the classes are the same objects as those of the ChatService) and "" for scripts."""
import importlib
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def registry_of(prefix="", **runs):
    loader = importlib.import_module(prefix + "extension_loader")
    registry = importlib.import_module(prefix + "task_registry").TaskRegistry()
    for name, run in runs.items():
        if run is not None:
            registry.register(loader.task_from_manifest(loader.read_manifest(os.path.join(REPO, "extensions", name)), run))
    return registry
