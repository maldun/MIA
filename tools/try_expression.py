"""
Tries the expression generator (expression_llm.py) with MIA's real language model, without the web page or the editor:
for each description the model is asked, the answer is validated like a preset and printed (nothing is saved, the presets and the feedback log
are temporary copies).

Run with the MIA virtualenv from the MIA folder (Ollama must run; MIA itself does not have to):
  python tools/try_expression.py "surprised but trying to hide it" "a sly grin" "very sleepy"
  python tools/try_expression.py --model gemma4:26b --temperature 0.4 "angry"
  python tools/try_expression.py --prompt "smug"      print the prompt that is sent (shape keys, rules, examples) and stop

Without arguments a few descriptions are tried. The model and options default to the ones MIA uses at the moment (the light profile), so Ollama
does not have to load a second model.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

from ollama import Client  # noqa: E402
from MIA.expression_llm import ExpressionGenerator  # noqa: E402
from MIA.preset_store import PresetStore, PresetError  # noqa: E402

DEFAULT_DESCRIPTIONS = ["surprised but trying to hide it", "a sly grin", "very sleepy", "shy and a little embarrassed", "proud and confident"]
SHIPPED = os.path.join(REPO, "ui", "godot", "presets")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("descriptions", nargs="*")
    parser.add_argument("--cfg", default=os.path.join(REPO, "setup_cfg.json"))
    parser.add_argument("--model", default=None, help="default: the light model of setup_cfg.json")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--prompt", action="store_true", help="only print the prompt for the first description")
    parser.add_argument("--keep", default=None, help="folder to keep the answers (JSON) in")
    args = parser.parse_args()

    with open(args.cfg) as fp:
        cfg = json.load(fp)
    profile_light = cfg.get("default_profile") == "light" and cfg.get("version_light")
    model = args.model or (cfg["version_light"] if profile_light else cfg["version"])
    options = dict((cfg.get("llm_options_light") if profile_light and not args.model else cfg.get("llm_options")) or {})
    options["temperature"] = args.temperature
    client = Client(host=f"http://{cfg.get('address', 'localhost')}:{cfg.get('port', 11434)}")

    def chat(messages, schema):
        reply = client.chat(model=model, messages=messages, format=schema, stream=False, options=options, think=False, keep_alive=cfg.get("keep_alive"))
        return reply["message"]["content"]

    work = tempfile.mkdtemp()
    store = PresetStore(os.path.join(work, "presets"), defaults_file=os.path.join(SHIPPED, "library.json"),
                        shape_keys_file=os.path.join(SHIPPED, "shape_keys.json"), gestures_file=os.path.join(SHIPPED, "gestures.json"))
    generator = ExpressionGenerator(store, chat, os.path.join(SHIPPED, "shape_keys.json"), os.path.join(SHIPPED, "gestures.json"),
                                    log_path=os.path.join(work, "feedback.jsonl"), model_name=lambda: model)
    descriptions = args.descriptions or DEFAULT_DESCRIPTIONS
    if args.prompt:
        for message in generator.messages(descriptions[0]):
            print(f"--- {message['role']} ---\n{message['content']}\n")
        return
    print(f"model {model}, options {options}\n")
    results = []
    for description in descriptions:
        started = time.time()
        try:
            result = generator.generate(description)
        except PresetError as exc:
            print(f"'{description}': FAILED ({exc.status}) {exc.message}\n")
            results.append({"description": description, "error": exc.message})
            continue
        except Exception as exc:
            print(f"'{description}': ERROR {exc!r}\n")
            sys.exit(1)
        preset = result["preset"]
        print(f"'{description}'  ({result['seconds']} s, closest existing preset: {result['closest']})")
        print(f"  says: {preset['description']}   tags: {', '.join(preset['tags'])}   gesture: {preset['gesture'] or '-'}")
        print("  weights: " + ", ".join(f"{k.replace('Fcl_', '')}={v}" for k, v in sorted(preset["weights"].items(), key=lambda kv: -kv[1])))
        if preset["bones"]:
            print("  bones: " + ", ".join(f"{k}={v}" for k, v in preset["bones"].items()))
        if result["corrections"]:
            print("  corrected: " + "; ".join(result["corrections"]))
        print()
        results.append({"description": description, "result": result})
    if args.keep:
        os.makedirs(args.keep, exist_ok=True)
        with open(os.path.join(args.keep, "answers.json"), "w") as fp:
            json.dump(results, fp, indent=2, ensure_ascii=False)
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
