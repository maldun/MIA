"""ports(real) and need(nodes): the subjects of an integration step (protected).

An integration step runs the scenario of its node with the parts integrated so far real and all others as mocks (decomposition.yaml, `integration`).
`ports(real)` gives every interface as a mock, or, for the interfaces in `real`, as the real provider of contract.py (skipped there until it is integrated).
`need(nodes)` skips a step until every node it needs is listed in READY. The integration of a node adds it to READY and gives the real adapter to
contract.py; both edits are amendments of this protected file, made with the owner.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "mocks"))

from contract import subject_for  # noqa: E402

READY = set()    # nodes whose integration step has been done, e.g. {"N-3.2"}

PYTHON_INTERFACES = ("IF-101", "IF-102", "IF-103", "IF-104", "IF-105", "IF-201", "IF-202", "IF-203", "IF-204", "IF-301", "IF-302", "IF-401", "IF-402", "IF-404", "IF-405")


def need(nodes):
    missing = [n for n in nodes if n not in READY]
    if missing:
        raise unittest.SkipTest("%s not integrated yet" % ", ".join(missing))


def ports(real=()):
    return {i: subject_for(i, "real" if i in real else "mock") for i in PYTHON_INTERFACES}
