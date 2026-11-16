"""
For the tests that import MIA's code by its plain module names (`import common_operations`, `import toolbox`): while their module runs the package `MIA` must not be importable.
The code that a transform runs does `from MIA import common_operations` first and falls back to the plain name; once another test has made the package importable (checkout_copy.use(),
`import MIA.web_app`) that import succeeds and gives a second `common_operations` without the node call that the test registered on the plain one (F-3 of G-V3.REPORT: 12 failures that
appeared only in a full run). The package and the folders that make it importable are taken away in setUpModule and put back in tearDownModule, so the modules that need the package find it again.

    import plain_modules
    setUpModule, tearDownModule = plain_modules.hooks()
"""
import os
import sys


def _is_package(name):
    return name == "MIA" or name.startswith("MIA.")


def hide_package():
    """takes MIA and MIA.* out of sys.modules and the sys.path entries that hold a folder MIA/ (the links of checkout_copy) off sys.path; returns what restore_package puts back"""
    modules = {name: module for name, module in sys.modules.items() if _is_package(name)}
    for name in modules:
        del sys.modules[name]
    path = list(sys.path)
    sys.path[:] = [entry for entry in path if not os.path.isdir(os.path.join(entry or os.curdir, "MIA"))]
    return modules, path


def restore_package(hidden):
    """puts back what hide_package took away (and forgets what was imported of MIA in the meantime)"""
    modules, path = hidden
    for name in [name for name in sys.modules if _is_package(name)]:
        del sys.modules[name]
    sys.modules.update(modules)
    sys.path[:] = path


def hooks():
    """(setUpModule, tearDownModule) for a test module that imports MIA's code by its plain names"""
    state = {}

    def set_up():
        state["hidden"] = hide_package()

    def tear_down():
        restore_package(state.pop("hidden"))
    return set_up, tear_down
