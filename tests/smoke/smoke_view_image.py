"""
Smoke check SMOKE-VIEW-001 of G-V4.VIEW (REQ-OPR-011; TR-VIEW-007, TR-VIEW-016): the release image opens the owner's PostgreSQL store.

On the owner's host (Deploy), after `deploy/up.sh` built the release image and started the stack with `store: database` and the owner's
MIA_DATABASE_URL (deploy/.env):
  1. `import psycopg` runs in the release image (a throw-away container without network);
  2. GET /api/v2/store, as the owner logged in through /api/login, answers `store` `database` and `reachable` true.
Nothing is written: one login and two GETs (TR-VIEW-016). The login is the owner's own account; its password comes from the environment
variable MIA_SMOKE_PASSWORD and is never printed.
Protected: change only through a plan amendment. Run:
  python tests/smoke/smoke_view_image.py --user <owner> [--url https://localhost] [--image localhost/mia:latest]   (exit 0 = green, 1 = red, 2 = cannot run)
"""
import argparse
import http.cookiejar
import json
import os
import ssl
import subprocess
import sys
import urllib.request


def image_has_psycopg(image):
    if subprocess.run(["podman", "image", "exists", image]).returncode != 0:
        return None, "the image %s does not exist (build it with deploy/up.sh)" % image
    done = subprocess.run(["podman", "run", "--rm", "--network", "none", "--entrypoint", "python", image, "-c", "import psycopg; print(psycopg.__version__)"],
                          capture_output=True, text=True, timeout=300)
    return done.returncode == 0, (done.stdout or done.stderr).strip()[-300:]


def store_answer(url, user, password):
    context = ssl.create_default_context()
    if url.startswith("https://localhost") or url.startswith("https://127.0.0.1"):
        context.check_hostname, context.verify_mode = False, ssl.CERT_NONE        # the stack's own certificate on this host
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), urllib.request.HTTPSHandler(context=context))
    login = urllib.request.Request(url + "/api/login", data=json.dumps({"user": user, "password": password}).encode(), method="POST",
                                   headers={"Content-Type": "application/json", "Origin": url})
    opener.open(login, timeout=30).read()
    with opener.open(url + "/api/v2/store", timeout=30) as answer:
        return json.loads(answer.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--user", required=True)
    parser.add_argument("--url", default="https://localhost")
    parser.add_argument("--image", default=os.environ.get("MIA_IMAGE", "localhost/mia:latest"))
    args = parser.parse_args()
    password = os.environ.get("MIA_SMOKE_PASSWORD")
    if not password:
        print("cannot run: set MIA_SMOKE_PASSWORD to the owner's password")
        return 2
    ok, note = image_has_psycopg(args.image)
    if ok is None:
        print("cannot run: " + note)
        return 2
    print("import psycopg in %s: %s (%s)" % (args.image, "yes" if ok else "NO", note))
    try:
        store = store_answer(args.url.rstrip("/"), args.user, password)
    except Exception as err:                                     # the stack does not answer: the check cannot run
        print("cannot run: the stack at %s does not answer: %s" % (args.url, err))
        return 2
    print("GET /api/v2/store: %s" % json.dumps(store))
    green = ok and store.get("store") == "database" and store.get("reachable") is True
    print("SMOKE-VIEW-001 " + ("green" if green else "red"))
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
