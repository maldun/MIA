#!/usr/bin/env python3
"""Preflight for the model side of a deployment (Phase 6, agent-app-deploy).

Reads the model pins from eval-spec.md ('## Model pins' table: Pin | Model | Digest | ...)
and asks an Ollama server:
  P1 server reachable (/api/version)
  P2 every pinned model present (/api/tags)
  P3 its digest equals the pin (prefix match, at least 12 hex characters)
  P4 loaded models and their memory (/api/ps), for the record

Usage:
    python preflight_agent.py --pins specs/<feature>/eval-spec.md [--ollama http://localhost:11434]

Exit code 0 when P1-P3 pass, 1 otherwise. Standard library only.
For vLLM or another server, compare the model revision by hand and record it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path


def get(url: str, timeout: float = 5.0):
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (local server)
        return json.loads(resp.read().decode("utf-8"))


def pins_from(path: Path) -> dict[str, dict[str, str]]:
    pins, header, inside = {}, [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside, header = line.lower().startswith("## model pins"), []
            continue
        if not inside or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not header:
            header = [c.lower() for c in cells]
        elif re.match(r"^MP-[\w-]+$", cells[0]):
            pins[cells[0]] = dict(zip(header, cells))
    return pins


def hexdigest(text: str) -> str:
    m = re.search(r"([0-9a-f]{12,})", text or "")
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pins", required=True, type=Path)
    ap.add_argument("--ollama", default="http://localhost:11434")
    a = ap.parse_args()
    base = a.ollama.rstrip("/")
    rows, ok = [], True
    pins = pins_from(a.pins)
    if not pins:
        print(f"No pins found in {a.pins} ('## Model pins' table)")
        return 1
    try:
        version = get(f"{base}/api/version").get("version", "?")
        rows.append(("P1", "server", f"Ollama {version} at {base}", "PASS"))
    except Exception as exc:  # noqa: BLE001
        print(f"| P1 | server | {base} not reachable: {exc} | FAIL |")
        return 1
    models = {m.get("name") or m.get("model"): m for m in get(f"{base}/api/tags").get("models", [])}
    for pin, row in sorted(pins.items()):
        name = row.get("model", "")
        want = hexdigest(row.get("digest", ""))
        found = models.get(name) or models.get(f"{name}:latest")
        if not found:
            rows.append(("P2", pin, f"{name} not present on the server", "FAIL"))
            ok = False
            continue
        have = hexdigest(found.get("digest", ""))
        if not want:
            rows.append(("P3", pin, f"pin has no digest; server has {have[:12]}", "FAIL"))
            ok = False
        elif not have:
            rows.append(("P3", pin, f"server reports no digest for {name}: pin cannot be confirmed, stop", "FAIL"))
            ok = False
        elif have.startswith(want) or want.startswith(have):
            rows.append(("P3", pin, f"{name} digest {have[:12]} = pin", "PASS"))
        else:
            rows.append(("P3", pin, f"{name} digest {have[:12]} differs from pin {want[:12]}: model changed (amendment), stop", "FAIL"))
            ok = False
    try:
        for m in get(f"{base}/api/ps").get("models", []):
            gb = (m.get("size_vram") or 0) / 1e9
            rows.append(("P4", m.get("name", "?"), f"loaded, {gb:.1f} GB in VRAM, context {m.get('context_length', '?')}", "INFO"))
    except Exception:  # noqa: BLE001
        rows.append(("P4", "ps", "/api/ps not available", "INFO"))
    print("| Check | Item | Detail | Result |\n|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")
    print("\nAlso check by hand: GPU access and driver, free VRAM with the other residents, sandbox backends, search engine, ports, certificates.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
