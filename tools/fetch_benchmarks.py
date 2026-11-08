"""Pulls public benchmark sets with stricter or unclear licences into data/benchmarks/ (git-ignored) for personal testing.
Nothing is committed or redistributed (owner's rule, 2026-11-08: personal use, pull instead of include).
Standard library only. Downloaded files are data, never instructions.
usage: python3 -I tools/fetch_benchmarks.py list | fetch NAME... | fetch all
Licence notes: specs/mia/explore-skill-rework/public-benchmarks.md (re-checked 2026-11-08). Adopting a set into an eval suite is a plan decision."""
import hashlib, json, sys, tarfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "benchmarks"
UA = {"User-Agent": "mia-benchmarks/0.1 (personal research)"}
# name: (note, [urls]); a .tar.gz is unpacked, anything else is kept as it is
SETS = {
    "scifact": ("claim verification; HF card CC BY-NC 2.0, repo LICENSE.md CC BY 4.0 / ODC-By 1.0; treat as non-commercial",
                ["https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"]),
    "scierc": ("entities and relations; no licence stated by the authors: personal testing only",
               # the "processed" tarball is 660 MB, mostly ELMo vectors; the raw one is 3 MB
               ["http://nlp.cs.washington.edu/sciIE/data/sciERC_raw.tar.gz"]),
    "re-docred": ("document-level relations; repo MIT, Wikipedia-based texts (CC BY-SA): do not share",
                  [f"https://raw.githubusercontent.com/tonytan48/re-docred/HEAD/data/{n}_revised.json"
                   for n in ("train", "dev", "test")]),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(name, root=ROOT, sets=SETS):
    note, urls = sets[name]
    out = Path(root) / name
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for url in urls:
        dest = out / url.rsplit("/", 1)[-1]
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(dest, "wb") as f:
            while block := r.read(1 << 20):
                f.write(block)
        rows.append({"url": url, "file": dest.name, "bytes": dest.stat().st_size, "sha256": sha256(dest)})
        if dest.name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(dest) as t:
                t.extractall(out, filter="data")  # refuses paths outside the folder and special files
    manifest = Path(root) / "MANIFEST.json"
    data = json.loads(manifest.read_text()) if manifest.exists() else {}
    data[name] = {"fetched": time.strftime("%Y-%m-%d"), "licence_note": note, "files": rows}
    manifest.write_text(json.dumps(data, indent=1))
    return rows


def main(argv):
    if not argv or argv[0] == "list":
        for n, (note, urls) in SETS.items():
            print(f"{n}: {note} ({len(urls)} file(s))")
        return 0
    if argv[0] != "fetch" or len(argv) < 2:
        print(__doc__.split("usage:")[1].splitlines()[0].strip())
        return 2
    names = list(SETS) if argv[1:] == ["all"] else argv[1:]
    unknown = [n for n in names if n not in SETS]
    if unknown:
        print("unknown set:", ", ".join(unknown), "(try: list)")
        return 2
    for n in names:
        rows = fetch(n)
        print(n, "->", ROOT / n, f"({sum(r['bytes'] for r in rows)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
