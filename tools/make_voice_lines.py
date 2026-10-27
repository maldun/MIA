#!/usr/bin/env python3
"""Makes the default voice lines (REQ-VOI-004): renders the texts of library/voice_line_texts.json with MIA's own TTS (Kokoro) and voice effect,
writes voice/expressions/<mood>_default.wav and lists the files in library/voice_lines.json. No third-party recording is used.
Run on the host with the MIA virtualenv, from the MIA folder:  python tools/make_voice_lines.py [--only happy,sad]
The texts are the provenance of the clips: change a text and run again."""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_lines(texts, speaker, folder, config_path):
    """renders one clip per mood and puts it in the "lines" of the config; returns the moods that got a clip"""
    os.makedirs(folder, exist_ok=True)
    with open(config_path, encoding="utf-8") as fp:
        config = json.load(fp)
    done = []
    for mood, text in texts.items():
        name = "%s_default.wav" % mood
        if speaker.render_voice(text, os.path.join(folder, name)) > 0:
            config.setdefault("lines", {})[mood] = [name]
            done.append(mood)
    with open(config_path, "w", encoding="utf-8") as fp:
        json.dump(config, fp, indent=2, ensure_ascii=False)
        fp.write("\n")
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--only", default="", help="comma separated moods; default all of the texts file")
    args = parser.parse_args()
    sys.path.insert(0, os.path.dirname(ROOT))
    from MIA.speak import Speaker
    with open(os.path.join(ROOT, "library", "voice_line_texts.json"), encoding="utf-8") as fp:
        texts = json.load(fp)
    if args.only:
        texts = {mood: texts[mood] for mood in args.only.split(",")}
    with open(os.path.join(ROOT, "setup_cfg.json"), encoding="utf-8") as fp:
        cfg = json.load(fp)
    cfg["address"] = None                       # render only, no web server to upload to
    done = make_lines(texts, Speaker(**cfg), os.path.join(ROOT, "voice", "expressions"), os.path.join(ROOT, "library", "voice_lines.json"))
    print("made: %s" % ", ".join(done))


if __name__ == "__main__":
    main()
