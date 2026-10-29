#!/usr/bin/env python3
"""
A readable preview of what an amendment would change in one file, for the shell (used by tools/amendment_lib.sh with --report; usable alone).

  python3 tools/amendment_report.py INSTALLED DRAFT [--color auto|always|never] [--context N]
  python3 tools/amendment_report.py --git COMMIT [--path specs/] [--repo DIR]     what a commit (an installed amendment) changed

  - changed words are marked inside the line:  hard cap of [-600-]{+1800+} seconds   (with colours: removed white on red, added black on green;
    the fields Text, Acceptance criterion and History of a requirement are highlighted)
  - requirements.md: by requirement, only the fields that changed, new and removed requirements named
  - other text and code: by line with line numbers (~ changed, + added, - removed), unchanged runs folded
  - the generated model block of architecture.sysml: only counted (it follows the requirement files)
Standard library only. Prints nothing but the report; changes no file.
"""
import argparse
import difflib
import re
import sys

RED, GREEN, DIM, BOLD, RESET = "\x1b[31m", "\x1b[32m", "\x1b[2m", "\x1b[1m", "\x1b[0m"
REMOVED_WORD, ADDED_WORD = "\x1b[1;37;41m", "\x1b[1;30;42m"        # changed words: white on red, black on green (also readable without the markers [- -] {+ +})
NEW, GONE, CHANGED, KEY = "\x1b[1;32m", "\x1b[1;31m", "\x1b[1;33m", "\x1b[1;36m"
KEY_FIELDS = ("Text", "Acceptance criterion", "History")           # the fields one reads first in a requirement
TOKEN = re.compile(r"\s+|\w+|[^\w\s]")
GEN_BEGIN, GEN_END = "// BEGIN GENERATED", "// END GENERATED"


def _paint(text, code, color):
    return "%s%s%s" % (code, text, RESET) if color else text


def word_diff(old, new, color=False):
    """old and new as one text with the changes marked: [-removed-] and {+added+}"""
    a, b = TOKEN.findall(old), TOKEN.findall(new)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append("".join(a[i1:i2]))
            continue
        if i2 > i1:
            out.append(_paint("[-%s-]" % "".join(a[i1:i2]), REMOVED_WORD, color))
        if j2 > j1:
            out.append(_paint("{+%s+}" % "".join(b[j1:j2]), ADDED_WORD, color))
    return "".join(out)


def _similar(old, new):
    """true when the change is a few words inside a sentence that stays the same; a sentence that was rewritten reads better as two lines"""
    a, b = TOKEN.findall(old), TOKEN.findall(new)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = {op for op, *_ in matcher.get_opcodes()}
    return ops <= {"equal", "insert"} or ops <= {"equal", "delete"} or matcher.ratio() >= 0.75      # only added or only removed words always read well inline


def _label(key, color):
    """the name of a field; the fields one reads first are highlighted, the others are dimmed"""
    return _paint(key + ":", KEY if key in KEY_FIELDS else DIM, color) + " "


def _change(key, old, new, color, indent="    "):
    """the lines that show how `old` became `new` in the field `key`"""
    if _similar(old, new):
        return ["%s%s%s" % (indent, _label(key, color), word_diff(old, new, color))]
    return ["%s%s(rewritten)" % (indent, _label(key, color)), "%s  %s %s" % (indent, _paint("-", GONE, color), _paint(old, RED, color)),
            "%s  %s %s" % (indent, _paint("+", NEW, color), _paint(new, GREEN, color))]


# --- by requirement --------------------------------------------------------------------------------------------------------------------

def _blocks(text):
    """(preamble, {id: (title, [(field, value), ...], raw)}, order) of a requirements.md; a block starts with `### ID – title`"""
    parts = re.split(r"(?m)^(?=### )", text)
    pre, blocks, order = parts[0], {}, []
    for part in parts[1:]:
        head = part.split("\n", 1)[0]
        match = re.match(r"### (\S+)\s+[–-]\s+(.*)", head)
        if not match:
            pre += part
            continue
        fields = [(m.group(1), m.group(2)) for m in re.finditer(r"(?m)^- ([^:\n]+):[ ]?(.*)$", part)]
        blocks[match.group(1)] = (match.group(2), fields, part)
        order.append(match.group(1))
    return pre, blocks, order


def _requirements(old, new, color):
    pre_old, old_blocks, _ = _blocks(old)
    pre_new, new_blocks, order = _blocks(new)
    lines = []
    if pre_old != pre_new:
        lines += ["~ text before the first requirement:"] + ["    " + l for l in _lines(pre_old, pre_new, 1, color)]
    for rid in order:
        title, fields, _ = new_blocks[rid]
        if rid not in old_blocks:
            lines.append("%s %s – %s" % (_paint("+ new     ", NEW, color), rid, title))
            first = next(((k, v) for k, v in fields if k == "Text"), None)
            if first:
                lines.append("    %s%s" % (_label("Text", color), _paint(first[1], GREEN, color)))
            continue
        old_title, old_fields, _ = old_blocks[rid]
        before, after = dict(old_fields), dict(fields)
        changes = []
        for key, value in fields:
            if key not in before:
                changes.append("    %s%s" % (_label(key, color), _paint("{+%s+}" % value, ADDED_WORD, color)))
            elif before[key] != value:
                changes += _change(key, before[key], value, color)
        for key, value in old_fields:
            if key not in after:
                changes.append("    %s%s" % (_label(key, color), _paint("[-%s-]" % value, REMOVED_WORD, color)))
        if old_title != title or changes:
            lines.append("%s %s – %s" % (_paint("~ changed ", CHANGED, color), rid, word_diff(old_title, title, color)))
            lines += changes
    for rid, (title, _, _) in old_blocks.items():
        if rid not in new_blocks:
            lines.append("%s %s – %s" % (_paint("- removed ", GONE, color), rid, title))
    return lines or ["no difference in the requirements"]


# --- by line ---------------------------------------------------------------------------------------------------------------------------

def _lines(old, new, context, color):
    a, b = old.splitlines(), new.splitlines()
    width = len(str(max(len(a), len(b), 1)))
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out, last_end = [], 0
    for group in matcher.get_grouped_opcodes(context):
        start = group[0][3]
        if start > last_end:
            out.append(_paint("   … %d unchanged lines …" % (start - last_end), DIM, color))
        for op, i1, i2, j1, j2 in group:
            if op == "equal":
                out += ["  %s: %s" % (str(j1 + k + 1).rjust(width), _paint(a[i1 + k], DIM, color)) for k in range(i2 - i1)]
                continue
            pairs = min(i2 - i1, j2 - j1) if op == "replace" else 0
            paired = [k for k in range(pairs) if _similar(a[i1 + k], b[j1 + k])]
            for k in range(pairs):
                if k in paired:
                    out.append("%s %s: %s" % (_paint("~", CHANGED, color), str(j1 + k + 1).rjust(width), word_diff(a[i1 + k], b[j1 + k], color)))
            for k in range(i1, i2):
                if not (0 <= k - i1 < pairs and k - i1 in paired):
                    out.append("%s %s: %s" % (_paint("-", GONE, color), str(k + 1).rjust(width), _paint(a[k], RED, color)))
            for k in range(j1, j2):
                if not (0 <= k - j1 < pairs and k - j1 in paired):
                    out.append("%s %s: %s" % (_paint("+", NEW, color), str(k + 1).rjust(width), _paint(b[k], GREEN, color)))
        last_end = group[-1][4]
    if matcher.get_grouped_opcodes(context) and last_end < len(b):
        out.append(_paint("   … %d unchanged lines …" % (len(b) - last_end), DIM, color))
    return out


def _model(old, new, color):
    def split(text):
        lines, head, gen, tail, state = text.splitlines(), [], [], [], 0
        for line in lines:
            if line.startswith(GEN_BEGIN):
                state = 1
            (gen if state == 1 else tail if state == 2 else head).append(line)
            if line.startswith(GEN_END):
                state = 2
        return head, gen, tail
    (h1, g1, t1), (h2, g2, t2) = split(old), split(new)
    out = []
    rest_old, rest_new = "\n".join(h1 + t1), "\n".join(h2 + t2)
    if rest_old != rest_new:
        out += _lines(rest_old, rest_new, 2, color)
    if g1 != g2:
        added = removed = 0
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, g1, g2, autojunk=False).get_opcodes():
            if op != "equal":
                removed += i2 - i1
                added += j2 - j1
        out.append("%s generated block (follows the requirement files, not read line by line): +%d -%d lines" % (_paint("~", CHANGED, color), added, removed))
    return out or ["no difference"]


def report_text(old, new, name, color=False, context=2):
    """the report for one file as text; old is None when the installed file does not exist"""
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    if old is None:
        lines = new.splitlines()
        shown = ["   " + l for l in lines[:12]]
        return "\n".join(["%s, %d lines" % (_paint("new file", GREEN, color), len(lines))] + shown + (["   … %d more lines …" % (len(lines) - 12)] if len(lines) > 12 else []))
    if old == new:
        return "no difference"
    if base.endswith("requirements.md"):
        body = _requirements(old, new, color)
    elif base.endswith(".sysml"):
        body = _model(old, new, color)
    else:
        body = _lines(old, new, context, color)
    return "\n".join(body)


def _git(repo, *args):
    import subprocess
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def report_commit(commit, repo=".", paths=(), color=False, context=2):
    """what a commit changed, file by file in the same readable form (an installed amendment, for example)"""
    listed = _git(repo, "diff-tree", "--no-commit-id", "--name-status", "-r", "--root", commit)
    if listed.returncode != 0:
        raise SystemExit("git: " + listed.stderr.strip())
    out = []
    for row in listed.stdout.splitlines():
        status, _, path = row.partition("\t")
        if paths and not any(path.startswith(p) for p in paths):
            continue
        if status.startswith("D"):
            out.append("%s %s\n   %s" % ("──", path, _paint("removed file", GONE, color)))
            continue
        new = _git(repo, "show", "%s:%s" % (commit, path))
        old = _git(repo, "show", "%s^:%s" % (commit, path))
        if new.returncode != 0:
            continue
        out.append("%s %s\n%s" % ("──", _paint(path, BOLD, color), "\n".join("   " + l for l in report_text(old.stdout if old.returncode == 0 else None, new.stdout, path, color=color, context=context).splitlines())))
    return "\n\n".join(out) or "no file changed"


def main(argv=None):
    parser = argparse.ArgumentParser(description="readable preview of the change of one file, or of the files of a commit (--git)")
    parser.add_argument("installed", nargs="?")
    parser.add_argument("draft", nargs="?")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    parser.add_argument("--context", type=int, default=2)
    parser.add_argument("--git", metavar="COMMIT", help="show what this commit changed instead of comparing two files")
    parser.add_argument("--repo", default=".", help="the repository for --git")
    parser.add_argument("--path", action="append", default=[], help="with --git: only the files below this path (repeatable)")
    args = parser.parse_args(argv)
    color = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())
    if args.git:
        print(report_commit(args.git, args.repo, args.path, color=color, context=args.context))
        return 0
    if not (args.installed and args.draft):
        parser.error("name the installed file and the draft, or use --git COMMIT")
    try:
        with open(args.installed, encoding="utf-8") as handle:
            old = handle.read()
    except FileNotFoundError:
        old = None
    with open(args.draft, encoding="utf-8") as handle:
        new = handle.read()
    print(report_text(old, new, args.draft, color=color, context=args.context))
    return 0


if __name__ == "__main__":
    sys.exit(main())
