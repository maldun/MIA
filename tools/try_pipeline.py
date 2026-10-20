"""
Runs a skill with MIA's real language model, without the web page: the events of the pipeline are printed as they happen (playful line and the accurate
description in brackets), then the answer. Runs are logged to a temporary folder (or --runs).

Run with the MIA virtualenv from the MIA folder (Ollama must run; MIA itself does not have to):
  python tools/try_pipeline.py summarize "A long text ..."
  python tools/try_pipeline.py summarize --file notes.txt --input sentences=2
  python tools/try_pipeline.py --check                       validate all skills and their pipelines, then stop
  python tools/try_pipeline.py summarize --model gemma4:26b "..."

The text is the input "text"; more inputs with --input name=value. The profile of the skill decides the model (light/full/current = the chat's), --model overrides it.
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
from MIA.config import default_path as default_config  # noqa: E402

from ollama import Client  # noqa: E402
from MIA.core import Core  # noqa: E402
from MIA.library import Library  # noqa: E402
from MIA.sandbox import create_router  # noqa: E402
from MIA.pipeline import PipelineError  # noqa: E402
from MIA.pipeline_model import OllamaModel  # noqa: E402


def show(event):
    if event["kind"] == "start":
        print("  %5.1fs  %s" % (event["at"], ("%s (%s)" % (event["playful"], event["plain"])) if event["playful"] else event["plain"]))
    elif event["kind"] in ("retry", "error"):
        print("  %5.1fs  [%s] %s" % (event["at"], event["kind"], event["plain"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill", nargs="?")
    parser.add_argument("text", nargs="*", help="the text (several words are joined)")
    parser.add_argument("--file", help="read the text from a file")
    parser.add_argument("--input", action="append", default=[], help="more inputs: name=value (numbers are numbers)")
    parser.add_argument("--cfg", default=default_config(REPO))
    parser.add_argument("--model", default=None)
    parser.add_argument("--runs", default=None, help="folder for the run log (default: temporary)")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_intermixed_args()

    with open(args.cfg) as fp:
        cfg = json.load(fp)
    profiles = {"full": (cfg["version"], cfg.get("llm_options")), "light": (cfg.get("version_light"), cfg.get("llm_options_light"))}
    current = profiles["light"] if cfg.get("default_profile") == "light" and cfg.get("version_light") else profiles["full"]
    client = Client(host=f"http://{cfg.get('address', 'localhost')}:{cfg.get('port', 11434)}")
    model = OllamaModel(client, lambda p: profiles.get(p) if profiles.get(p, (None,))[0] else None, lambda: current, keep_alive=cfg.get("keep_alive"))
    work = tempfile.mkdtemp()
    library = Library(os.path.join(REPO, cfg.get("library_dir", "library")), os.path.join(REPO, cfg.get("user_library_dir", "data/library")),
                      os.path.join(work, "library.sqlite"))
    core = Core(os.path.join(REPO, cfg.get("skills_dir", "skills")), library, args.runs or work, model=model, functions={"converse": None}, sandbox=create_router(cfg))
    problems = core.check()
    for name, found in problems.items():
        print("PROBLEM %s: %s" % (name, "; ".join(found)))
    if args.check:
        print("skills: %s" % ", ".join(core.skills.names()))
        sys.exit(1 if problems else 0)
    if not args.skill:
        parser.error("name a skill (or use --check)")
    inputs = {"text": open(args.file, encoding="utf-8").read() if args.file else " ".join(args.text)}
    for item in args.input:
        key, _, value = item.partition("=")
        inputs[key] = int(value) if value.isdigit() else (json.loads(value) if value[:1] in "{[" else value)       # numbers and JSON are understood
    inputs.setdefault("sentences", 3)
    if args.model:
        core.skills.get(args.skill)["model"] = {"name": args.model}
    print("skill %s\n" % args.skill)
    try:
        result = core.run(args.skill, inputs, on_event=show)
    except PipelineError as exc:
        print("cannot run: %s" % exc)
        sys.exit(1)
    print("\nstatus %s in %.1fs" % (result.status, result.seconds))
    if result.error:
        print("error:", result.error)
    print(json.dumps(result.answer, indent=1, ensure_ascii=False))
    print("\nrun log: %s" % core.run_log.folder)


if __name__ == "__main__":
    main()
