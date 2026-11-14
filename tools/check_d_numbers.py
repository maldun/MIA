"""
Checks the decision numbers (D-nnn) of specs/mia/review-log.md across all local branches and the working files of all worktrees: the same number defined
with different text on two lines of work collides at the merge. Prints the highest number per line of work, the next free number and every collision.
Exit code 1 when a number is defined twice with different text. usage: python3 -I tools/check_d_numbers.py   (any directory of the repository)
"""
import re
import subprocess
import sys

LOG = "specs/mia/review-log.md"
ROW = re.compile(r"^\| (D-\d+) \| (.*)$")


def git(*args, cwd=None):
    result = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return result.stdout if result.returncode == 0 else ""


def rows(text):
    """number -> normalized text of its row (whitespace collapsed, so a changed line ending is no collision)"""
    found = {}
    for line in text.splitlines():
        match = ROW.match(line)
        if match:
            found[match.group(1)] = " ".join(match.group(2).split())
    return found


def main():
    sources = {}
    for branch in git("for-each-ref", "--format=%(refname:short)", "refs/heads").split():
        sources["branch " + branch] = rows(git("show", "%s:%s" % (branch, LOG)))
    for line in git("worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line.split(" ", 1)[1]
            try:
                with open("%s/%s" % (path, LOG), encoding="utf-8") as handle:
                    sources["files " + path] = rows(handle.read())          # includes what is not committed yet
            except OSError:
                pass
    sources = {name: found for name, found in sources.items() if found}
    number = lambda key: int(key[2:])
    highest = {name: max(found, key=number) for name, found in sources.items()}
    for name in sorted(sources, key=lambda n: number(highest[n])):
        print("%-6s %s" % (highest[name], name))
    owners = {}
    for name, found in sources.items():
        for key, text in found.items():
            owners.setdefault(key, {}).setdefault(text, []).append(name)
    clashes = {key: variants for key, variants in owners.items() if len(variants) > 1}
    top = max(number(key) for key in owners)
    print("next free: D-%d" % (top + 1))
    for key in sorted(clashes, key=number):
        print("COLLISION %s: %d different texts" % (key, len(clashes[key])))
        for text, names in clashes[key].items():
            print("  %s ... in %s" % (text[:70], ", ".join(names[:3]) + (" +%d" % (len(names) - 3) if len(names) > 3 else "")))
    if not clashes:
        print("no collisions")
    return 1 if clashes else 0


if __name__ == "__main__":
    sys.exit(main())
