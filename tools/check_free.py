"""Free and open (REQ-OPR-009, TC-OPR-009): MIA is GPL-3.0-or-later and uses no paid API.

Checks three things: LICENSE is the GPL version 3 text and README.md grants "any later version"; no requirement file lists a client library of a
paid API; no web log (data/runs/web-YYYY-MM.jsonl, written by web_tools and scholar) holds a request to a paid API host.
The two lists below are the one place where paid APIs are named; extend them when a new one turns up.
    python tools/check_free.py [--repo DIR] [--log FILE ...]      (without --log: every web log of DIR/data/runs)
Exit 0 and "free and open ..." when nothing is found, else exit 1 and one line per problem.
"""
import argparse
import glob
import json
import os
import re
import sys
from urllib.parse import urlsplit

PAID_PACKAGES = frozenset((
    "openai", "anthropic", "google-generativeai", "google-genai", "google-cloud-aiplatform", "vertexai", "cohere", "mistralai", "groq",
    "together", "replicate", "voyageai", "ai21", "fireworks-ai", "elevenlabs", "deepl", "azure-ai-inference", "azure-cognitiveservices-speech",
    "boto3-bedrock", "perplexityai", "serpapi", "google-search-results",
))
PAID_HOSTS = (
    "api.openai.com", "api.anthropic.com", "generativelanguage.googleapis.com", "aiplatform.googleapis.com", "api.cohere.ai", "api.cohere.com",
    "api.mistral.ai", "api.groq.com", "api.together.xyz", "api.replicate.com", "api.voyageai.com", "api.ai21.com", "api.fireworks.ai",
    "api.elevenlabs.io", "api.deepl.com", "api-free.deepl.com", "openai.azure.com", "api.perplexity.ai", "serpapi.com", "api.bing.microsoft.com",
)
GPL_TITLE = ("GNU GENERAL PUBLIC LICENSE", "Version 3, 29 June 2007")
OR_LATER = "version 3 of the License, or (at your option) any later version"
PACKAGE_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalized(name):
    """package names compare without case and with -, _ and . alike (PEP 503)"""
    return re.sub(r"[-_.]+", "-", name).lower()


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fp:
            return fp.read()
    except OSError:
        return ""


def licence_problems(repo):
    problems = []
    licence = read(os.path.join(repo, "LICENSE"))
    if not all(part in licence for part in GPL_TITLE):
        problems.append("LICENSE is not the text of the GNU GPL version 3")
    if OR_LATER not in " ".join(read(os.path.join(repo, "README.md")).split()):
        problems.append('README.md does not grant "%s"' % OR_LATER)
    return problems


def paid_packages(paths):
    found = []
    for path in paths:
        for line in read(path).splitlines():
            match = PACKAGE_NAME.match(line.split("#", 1)[0])
            if match and normalized(match.group(1)) in PAID_PACKAGES:
                found.append((path, normalized(match.group(1))))
    return found


def is_paid(host):
    return any(host == paid or host.endswith("." + paid) for paid in PAID_HOSTS)


def paid_hosts(paths):
    found = []
    for path in paths:
        for number, line in enumerate(read(path).splitlines(), 1):
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            host = (urlsplit(str(entry.get("url") or "")).hostname or "") if isinstance(entry, dict) else ""
            if is_paid(host):
                found.append((path, number, host))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--log", nargs="*", help="web logs (default: DIR/data/runs/web-*.jsonl)")
    args = parser.parse_args(argv)
    requirements = sorted(glob.glob(os.path.join(args.repo, "requirements*.txt")))
    logs = args.log if args.log is not None else sorted(glob.glob(os.path.join(args.repo, "data", "runs", "web-*.jsonl")))
    problems = licence_problems(args.repo)
    problems += ["%s: %s is a client of a paid API" % (path, package) for path, package in paid_packages(requirements)]
    problems += ["%s:%d: request to the paid API host %s" % (path, number, host) for path, number, host in paid_hosts(logs)]
    if problems:
        print("\n".join(problems))
        return 1
    print("free and open: GPL-3.0-or-later, %d requirement file(s) and %d web log(s) without a paid API" % (len(requirements), len(logs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
