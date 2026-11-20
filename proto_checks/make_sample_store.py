"""PROTOTYPE: builds a sample store of graphs in a folder (the 15 converted skill graphs and one graph with four versions by four authors).
Usage: python proto_checks/make_sample_store.py <folder>"""
import os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
from storage_files import FileBackend
from proto_checks.cp2_check import populate

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
backend = FileBackend(sys.argv[1])
populate(backend)
print("sample store in %s: %d graphs, %d step records" % (sys.argv[1], len(backend.ids("graphs")), len(backend.ids("graph_nodes"))))
