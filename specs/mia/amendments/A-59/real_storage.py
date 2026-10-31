_REAL_STORAGE = {}


def _real_storage_module(name):
    """A module of the real Storage layer (storage, storage_files, storage_postgres), loaded by file path together with the real graph_rules and
    graph_tables (A-59, D-162). The mocks have a module of the same name, graph_rules, and the mock side of a suite imports it first; a plain
    `import storage` (or a storage imported earlier in the process) then validated with the cached mock rules, so in a full run the real side of
    IF-102 tested the mock. Each module is loaded once per process; sys.modules is left as it was."""
    if name not in _REAL_STORAGE:
        import importlib.util
        chain = [n for n in ("graph_rules", "graph_tables", "storage", name) if n != name] + [name]
        saved = {n: sys.modules.get(n) for n in chain}
        try:
            for n in chain:
                if n not in _REAL_STORAGE:
                    spec = importlib.util.spec_from_file_location(n, os.path.join(REPO, n + ".py"))
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[n] = module
                    spec.loader.exec_module(module)
                    _REAL_STORAGE[n] = module
                sys.modules[n] = _REAL_STORAGE[n]
        finally:
            for n, module in saved.items():
                if module is None:
                    sys.modules.pop(n, None)
                else:
                    sys.modules[n] = module
    return _REAL_STORAGE[name]


