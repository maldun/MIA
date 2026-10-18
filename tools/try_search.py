"""
Tries the web tools without MIA: a search with the configured backends (SearXNG, then DuckDuckGo) and, if wanted, a fetch of the first results with the
safety rules. Everything is printed, including which backend answered and what the page looks like after the text extraction.

Run with the MIA virtualenv from the MIA folder:
  python tools/try_search.py "python asyncio tutorial"
  python tools/try_search.py --fetch 2 "python asyncio tutorial"      also fetch the first two results and show the start of their text
  python tools/try_search.py --url https://example.com                fetch one page
  python tools/try_search.py --backends duckduckgo "query"            only these backends (comma separated)
  python tools/try_search.py --safety                                 show which addresses the safety rules block

Settings come from setup_cfg.json (search_backends, searxng_url, ...). The web log of the trial is kept in a temporary folder that is printed at the end.
"""
import argparse
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

from MIA import web_tools  # noqa: E402

SAMPLE_ADDRESSES = ["http://127.0.0.1:8585/api/presets", "http://localhost:11434/api/tags", "http://192.168.0.1/", "http://169.254.169.254/latest/meta-data/",
                    "http://100.64.0.1/", "http://[::1]/", "file:///etc/passwd", "http://user:pw@example.com/", "http://example.com:22/", "https://example.com/"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", nargs="*")
    parser.add_argument("--cfg", default=os.path.join(REPO, "setup_cfg.json"))
    parser.add_argument("--fetch", type=int, default=0, help="fetch the first N results")
    parser.add_argument("--url", help="fetch this page")
    parser.add_argument("--backends", help="comma separated, overrides search_backends")
    parser.add_argument("--safety", action="store_true")
    args = parser.parse_intermixed_args()

    with open(args.cfg) as fp:
        cfg = json.load(fp)
    if args.backends:
        cfg["search_backends"] = args.backends.split(",")
    logs = tempfile.mkdtemp()

    if args.safety:
        for address in SAMPLE_ADDRESSES:
            try:
                web_tools.check_url(address)
                print("allowed  %s" % address)
            except web_tools.UnsafeUrl as exc:
                print("blocked  %s  (%s)" % (address, exc))
        return

    tools, search, client = web_tools.build_web_tools(cfg, logs)
    print("backends: %s\n" % ", ".join(b.name for b in search.backends))
    urls = [args.url] if args.url else []
    if args.query:
        try:
            found = tools["web_search"][0](" ".join(args.query))
        except web_tools.SearchError as exc:
            print("SEARCH FAILED: %s" % exc)
            for error in exc.errors:
                print("  -", error)
            sys.exit(1)
        print("answered by: %s" % found["backend"])
        for error in found["errors"] + found["warnings"]:
            print("  note: %s" % error)
        for number, result in enumerate(found["results"], 1):
            print("%2d. %s\n    %s\n    %s" % (number, result["title"], result["url"], result["snippet"][:160]))
        urls += [r["url"] for r in found["results"][:args.fetch]]
    for url in urls:
        print("\n--- fetch %s" % url)
        try:
            page = tools["fetch_page"][0](url)
        except web_tools.WebError as exc:
            print("  %s: %s" % (type(exc).__name__, exc))
            continue
        print("  title: %s | %d characters%s | content type %s" % (page["title"], len(page["text"]), " (clipped)" if page["clipped"] else "", page["content_type"]))
        if page["signals"]:
            print("  WARNING phrases that look like instructions to a model: %s" % ", ".join(page["signals"]))
        print("  " + page["text"][:500].replace("\n", "\n  "))
    print("\nweb log: %s" % logs)


if __name__ == "__main__":
    main()
