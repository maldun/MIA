"""
Tries the sandbox without MIA: which backends exist on this machine, which one each kind of operation would get, and a run of a script (yours or an example) with timing.

Run with the MIA virtualenv from the MIA folder:
  python tools/try_sandbox.py                                      the backends and the routing table
  python tools/try_sandbox.py --script 'result = sum(data["numbers"])' --data '{"numbers": [1, 2, 3]}'
  python tools/try_sandbox.py --script 'result = 1' --kind web_script        a strong operation (needs the podman backend)
  python tools/try_sandbox.py --backend podman --script ...                  force one backend
  python tools/try_sandbox.py --attack                                       a few hostile scripts (policy off) and what the wall does with them

The podman backend needs its image once: tools/sandbox/build_image.sh
"""
import argparse
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

from MIA import sandbox as S  # noqa: E402

ATTACKS = [
    ("read the host's /etc/passwd", "import os\nresult = [l.split(':')[0] for l in open('/etc/passwd')][:5] if os.path.exists('/etc/passwd') else 'no /etc/passwd'"),
    ("reach the internet", "import socket\ntry:\n    socket.create_connection(('1.1.1.1', 443), timeout=2)\n    result = 'REACHED THE INTERNET'\nexcept OSError as e:\n    result = 'blocked: ' + type(e).__name__"),
    ("start a process", "import os\ntry:\n    os.fork()\n    result = 'FORKED'\nexcept OSError as e:\n    result = 'blocked: errno %d' % e.errno"),
    ("write outside /tmp", "try:\n    open('/usr/hacked', 'w')\n    result = 'WROTE TO /usr'\nexcept OSError as e:\n    result = 'blocked: ' + type(e).__name__"),
    ("an endless loop", "while True:\n    pass"),
    ("eat memory", "x = bytearray(4 * 1024 ** 3)\nresult = len(x)"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--script")
    parser.add_argument("--data", default="{}")
    parser.add_argument("--kind", default="compute", choices=["compute", "web_script", "parse"])
    parser.add_argument("--origin", default="model", choices=["library", "model", "external"])
    parser.add_argument("--tainted", action="store_true")
    parser.add_argument("--high-stakes", action="store_true")
    parser.add_argument("--backend", choices=["bubblewrap", "podman"])
    parser.add_argument("--degrade", action="store_true")
    parser.add_argument("--attack", action="store_true")
    args = parser.parse_args()
    router = S.create_router({"sandbox_backend": args.backend or "auto", "sandbox_degrade": args.degrade})

    print("backends:")
    for name, backend in router.backends.items():
        info = backend.info()
        print("  %-11s %s" % (name, "available" if info["available"] else "NOT available: " + info["reason"]))
    print("\nwhich backend gets which operation:")
    for kind, origin, tainted, stakes in (("compute", "library", False, "normal"), ("compute", "model", False, "normal"), ("compute", "model", True, "normal"),
                                          ("web_script", "model", False, "normal"), ("parse", "library", False, "normal"), ("compute", "external", False, "normal"),
                                          ("compute", "library", False, "high")):
        operation = S.Operation(kind, origin, tainted, stakes)
        backend, tier, reasons = router.choose(operation)
        print("  %-10s %-9s tainted=%-5s stakes=%-6s -> %-10s (%s%s)" % (kind, origin, tainted, stakes, backend.name if backend else "REFUSED", tier, "; " + "; ".join(reasons) if reasons else ""))

    operation = S.Operation(args.kind, args.origin, args.tainted, "high" if args.high_stakes else "normal")
    if args.attack:
        backend = router.choose(operation)[0]
        if backend is None:
            print("\nno backend for this operation")
            return
        print("\nhostile scripts on %s (policy off, full builtins):" % backend.name)
        for label, code in ATTACKS:
            started = time.time()
            run = backend.run(code, policy=False, raw=True, timeout=3, memory_mb=256)
            print("  %-26s %-8s %-45s %.2fs" % (label, run.status, (run.result if run.status == "ok" else (run.error or {}).get("type", "")) if run.status != "timeout" else "killed by the timeout", time.time() - started))
        return
    if args.script:
        started = time.time()
        run = router.run(args.script, json.loads(args.data), operation=operation)
        print("\n%s on %s (%s tier%s) in %.2fs" % (run.status, run.backend or "-", run.tier, ", DEGRADED" if run.degraded else "", time.time() - started))
        print(json.dumps(run.as_dict(), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
