"""Test doubles for the snapshot checks (TC-WFM-061 to 066, G-V2.CONVERT): an in-memory library with the IF-203 v1 operations a snapshot needs and a stand-in
for the accounts. Complexity 2; they hold no rules of the product. The IF-203 v1 contract text is not reviewed yet (D-188): the operations named in
`snapshot_store.py` are an assumption of the tests."""


class LibraryLab:
    KINDS = ("skills", "workflows", "context_graphs", "transforms")

    def __init__(self, pins=None):
        self._docs, self._current, self._authors = {}, {}, {}      # (kind, id) -> [doc per version], current version, [author per version]
        self._trust, self._lifecycle = {}, {}
        self._pins = dict(pins or {})

    def list_ids(self, kind):
        return sorted(i for (k, i) in self._docs if k == kind)

    def save(self, kind, record_id, doc, author):
        key = (kind, record_id)
        self._docs.setdefault(key, []).append(doc)
        self._authors.setdefault(key, []).append(author)
        self._current[key] = len(self._docs[key])
        if kind == "transforms":
            self._trust.setdefault(record_id, "untrusted")
            self._lifecycle.setdefault(record_id, "draft")
        return {"version": self._current[key]}

    def read(self, kind, record_id, version=None):
        key = (kind, record_id)
        version = version or self._current[key]
        return {"version": version, "doc": self._docs[key][version - 1]}

    def history(self, kind, record_id):
        key = (kind, record_id)
        return [{"version": i + 1, "author": a} for i, a in enumerate(self._authors[key])]

    def restore(self, kind, record_id, version, author):
        """the item gets `version` as its current one; no version is created or deleted (assumption A1 of the tests, see the report)"""
        self._current[(kind, record_id)] = version
        return {"version": version}

    def get_trust(self, record_id):
        return self._trust[record_id]

    def set_trust(self, record_id, trust, author):
        self._trust[record_id] = trust

    def get_lifecycle(self, record_id):
        return self._lifecycle[record_id]

    def set_lifecycle(self, record_id, lifecycle, author):
        self._lifecycle[record_id] = lifecycle

    def pins(self):
        return dict(self._pins)

    # --- for the tests -----------------------------------------------------------------------------------------------------------------------
    def state(self):
        """the whole skill set as one comparable value: (kind, id, current version, doc, trust, lifecycle) per item, snapshots left out"""
        rows = []
        for kind in self.KINDS:
            for i in self.list_ids(kind):
                v = self._current[(kind, i)]
                rows.append((kind, i, v, repr(self._docs[(kind, i)][v - 1]), self._trust.get(i) if kind == "transforms" else None,
                             self._lifecycle.get(i) if kind == "transforms" else None))
        return rows

    def version_lists(self):
        """{(kind, id): [1, 2, ...]} of every item except snapshots"""
        return {(k, i): list(range(1, len(d) + 1)) for (k, i), d in self._docs.items() if k in self.KINDS}


class AccountsLab:
    """the owner is the account that creates accounts (REQ-WFM-066); a second account is created by it"""

    def __init__(self, owner="anna"):
        self.owner, self.accounts = owner, [owner]

    def create(self, by, name):
        if by != self.owner:
            raise PermissionError(by)
        self.accounts.append(name)

    def is_owner(self, account):
        return account == self.owner


def standard_state(lab, author="anna"):
    """the state of TC-WFM-061: 2 skills, 2 workflow graphs, 1 context graph, 3 transforms (trusted and tested, trusted and draft, untrusted and retired)"""
    for i in ("research", "verify_claim"):
        lab.save("skills", i, {"name": i, "v": 1}, author)
    for i in ("lookup", "compare"):
        lab.save("workflows", i, {"nodes": [i], "edges": []}, author)
    lab.save("context_graphs", "places", {"nodes": ["places"], "edges": []}, author)
    for i, trust, lifecycle in (("t_sum", "trusted", "tested"), ("t_draft", "trusted", "draft"), ("t_old", "untrusted", "retired")):
        lab.save("transforms", i, {"fn": i}, author)
        lab.set_trust(i, trust, author)
        lab.set_lifecycle(i, lifecycle, author)
