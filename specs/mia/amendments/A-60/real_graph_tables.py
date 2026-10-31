def _real_graph_tables():
    """graph_tables with the real graph_rules (A-60). The mocks have a module of the same name, graph_rules, and the mock side of a suite
    imports it first; a plain `import graph_tables` would then validate with the cached mock rules, so the real side tested the mock."""
    import importlib.util

    def load(name):
        spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    mock = sys.modules.get("graph_rules")
    sys.modules["graph_rules"] = load("graph_rules")
    try:
        return load("graph_tables")
    finally:
        if mock is None:
            sys.modules.pop("graph_rules")
        else:
            sys.modules["graph_rules"] = mock


