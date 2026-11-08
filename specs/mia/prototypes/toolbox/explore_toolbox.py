"""PROTOTYPE: look at the toolbox by hand. Status: Prototype, not verified.

  python explore_toolbox.py          guided tour (OC-1..OC-3), then the prompt
  python explore_toolbox.py --shell  prompt only
Prompt commands: help, who owner|guest, import [id] [version], look ID, list, trust ID trusted|untrusted, life ID draft|tested|retired [evidence|baseline],
export ID, run ID x, baseline ID x, seed, quit. 'import' makes a small sample transform that doubles x and writes a marker file when its code text runs.
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from toolbox import Toolbox, ToolboxError   # noqa: E402

NODES = pathlib.Path(__file__).resolve().parents[4] / "library" / "nodes"
MARKER = os.path.join(tempfile.gettempdir(), "toolbox_prototype_marker")


def sample(tid="ext.double", version=1):
    code = "open(%r, 'w').write('ran')\ndef run(a):\n    return a['x'] * 2 + %d\n" % (MARKER, version - 1)
    return json.dumps({"id": tid, "version": version, "status": "trusted", "inputs": {"type": "object"}, "outputs": {"type": "object"}, "code": code})


def show(item):
    print("  %s v%s | trust: %s | lifecycle: %s | origin: %s | baseline allowed: %s%s | marker file: %s" % (
        item["id"], item["version"], item["trust"], item["lifecycle"], item["origin"], item["baseline_ok"],
        " | reason: %s" % item["reason"] if item["reason"] else "", "present" if os.path.exists(MARKER) else "absent"))


def step(tb, who, line):
    """one command; errors of the toolbox are shown, not raised"""
    w = line.split()
    if not w:
        return
    cmd, a = w[0], w[1:]
    try:
        if cmd == "who":
            who[0] = a[0]
        elif cmd == "import":
            print("  imported", tb.import_transform(sample(a[0] if a else "ext.double", int(a[1]) if len(a) > 1 else 1)))
        elif cmd == "look":
            show(tb.look_up(a[0]))
        elif cmd == "list":
            ids = tb.offer()
            print("  offered: %d ids%s" % (len(ids), "" if len(ids) > 12 else ": " + ", ".join(ids)))
        elif cmd == "trust":
            tb.set_trust(a[0], a[1], who[0]); print("  ok")
        elif cmd == "life":
            extra = a[2] if len(a) > 2 else None
            tb.set_lifecycle(a[0], a[1], who[0], evidence=None if extra == "baseline" else extra, allow_baseline=extra == "baseline"); print("  ok")
        elif cmd == "export":
            print(" ", tb.export_transform(a[0]))
        elif cmd in ("run", "baseline"):
            print("  result:", tb.run(a[0], {"x": float(a[1])}, as_baseline=cmd == "baseline"))
        elif cmd == "seed":
            tb.seed_shipped(NODES); print("  seeded shipped nodes")
        else:
            print(__doc__)
    except ToolboxError as err:
        print("  REFUSED -", err)
    except (IndexError, ValueError, KeyError):
        print("  usage: see 'help'")


def tour(tb, who):
    if os.path.exists(MARKER):
        os.remove(MARKER)
    script = [("OC-1: a step from outside arrives; the file claims 'trusted'", ["who guest", "import", "look ext.double", "run ext.double 2"]),
              ("OC-2: a guest tries to trust it, then the owner does", ["trust ext.double trusted", "who owner", "trust ext.double trusted", "run ext.double 2"]),
              ("OC-3: retire it", ["life ext.double retired", "list", "run ext.double 2", "baseline ext.double 2"])]
    for title, lines in script:
        print("\n== " + title)
        for line in lines:
            print("> " + line)
            step(tb, who, line)


def main():
    tb, who = Toolbox(), ["owner"]
    if "--shell" not in sys.argv:
        tour(tb, who)
    print("\nYour turn (account: %s). Type 'help'." % who[0])
    while True:
        try:
            line = input("[%s]> " % who[0])
        except EOFError:
            break
        if line.strip() in ("quit", "exit"):
            break
        step(tb, who, line)


if __name__ == "__main__":
    main()
