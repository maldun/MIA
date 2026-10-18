"""
Measures MIA's voice: Kokoro (TTS) and RVC (voice change) per sentence, the first sentence after the start (models are loaded lazily),
and how much CPU it costs. Nothing is played or uploaded.

Run with the MIA virtualenv from the MIA folder (MIA itself does not have to run; Ollama is not needed):
  python tools/tts_benchmark.py                       the settings of setup_cfg.json
  python tools/tts_benchmark.py --stock               without MIA's optimizations (index cache, warm-up), for comparison
  python tools/tts_benchmark.py --f0 pm --threads 8   try other settings (f0 method, CPU threads, index_rate, ...)
  python tools/tts_benchmark.py --save out_dir        also keep the rendered sentences as WAV files to listen to
"""
import argparse
import json
import os
import resource
import shutil
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

SENTENCES = [
    "Hello! It is nice to see you again.",
    "I have been thinking about what you told me yesterday, and I think you were right.",
    "The weather looks good today, so maybe we could go for a walk later?",
    "Let me check that for you.",
    "There are three things we should keep in mind: time, money, and a little bit of patience.",
    "Good night, and sleep well!",
]


def cpu_seconds():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cfg", default=os.path.join(REPO, "setup_cfg.json"))
    parser.add_argument("--stock", action="store_true", help="switch MIA's optimizations off")
    parser.add_argument("--f0", default=None, help="f0 method of RVC (rmvpe, pm, harvest, crepe)")
    parser.add_argument("--index-rate", type=float, default=None)
    parser.add_argument("--threads", type=int, default=None, help="CPU threads (cpu_threads)")
    parser.add_argument("--no-rvc", action="store_true", help="Kokoro only")
    parser.add_argument("--pad", type=float, default=None, help="RVC padding in seconds on each side (rvc_pad; RVC's default on a CPU is 1)")
    parser.add_argument("--save", default=None, help="folder for the rendered WAV files")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    parser.add_argument("--models-root", default=REPO, help="MIA folder that has voice/models (not in version control, e.g. the main checkout)")
    args = parser.parse_args()

    with open(args.cfg) as fp:
        cfg = json.load(fp)
    kokoro = dict(cfg.get("kokoro_opts", {}))
    for key, default in (("model", "voice/models/kokoro/kokoro-v1.0.onnx"), ("voices", "voice/models/kokoro/voices-v1.0.bin")):
        path = kokoro.get(key, default)
        kokoro[key] = path if os.path.isabs(path) else os.path.join(args.models_root, path)
    cfg["kokoro_opts"] = kokoro
    if args.stock:
        cfg["rvc_cache_index"] = False
        cfg["tts_warmup"] = False
    if args.f0 or args.index_rate is not None:
        cfg["rvc_params"] = dict(cfg.get("rvc_params", {}))
        if args.f0:
            cfg["rvc_params"]["f0method"] = args.f0
        if args.index_rate is not None:
            cfg["rvc_params"]["index_rate"] = args.index_rate
    if args.threads:
        cfg["cpu_threads"] = args.threads
    if args.no_rvc:
        cfg["rvc_enabled"] = False
    if args.pad is not None:
        cfg["rvc_pad"] = args.pad
    if args.stock:
        cfg["rvc_pad"] = 1      # RVC's own padding on a CPU

    t0, c0 = time.perf_counter(), cpu_seconds()
    from MIA.speak import Speaker
    speaker = Speaker(**cfg)
    start_seconds, start_cpu = time.perf_counter() - t0, cpu_seconds() - c0

    stages = {}

    def timed(name, function):
        def wrapper(*a, **k):
            t, c = time.perf_counter(), cpu_seconds()
            try:
                return function(*a, **k)
            finally:
                stages[name] = (time.perf_counter() - t, cpu_seconds() - c)
        return wrapper

    speaker.text2speech = timed("tts", speaker.text2speech)
    if speaker._rvc_enabled:
        speaker.change_voice = timed("rvc", speaker.change_voice)

    out_dir = args.save or tempfile.mkdtemp()
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for number, sentence in enumerate(SENTENCES):
        stages.clear()
        path = os.path.join(out_dir, f"sentence{number + 1}.wav")
        t, c = time.perf_counter(), cpu_seconds()
        audio = speaker.render_voice(sentence, path)
        total, cpu = time.perf_counter() - t, cpu_seconds() - c
        rows.append({"sentence": number + 1, "audio": audio, "total": total, "cpu": cpu,
                     "tts": stages.get("tts", (0, 0))[0], "rvc": stages.get("rvc", (0, 0))[0]})
    if not args.save:
        shutil.rmtree(out_dir, ignore_errors=True)

    warm = rows[1:]
    audio = sum(r["audio"] for r in warm)
    result = {
        "settings": {"stock": args.stock, "f0": cfg.get("rvc_params", {}).get("f0method"), "rvc": cfg.get("rvc_enabled", True),
                     "threads": cfg.get("cpu_threads"), "pad": cfg.get("rvc_pad", "0.25 (MIA default)"), "index_rate": cfg.get("rvc_params", {}).get("index_rate", "default 0.5")},
        "start_seconds": round(start_seconds, 2), "start_cpu": round(start_cpu, 1),
        "first_sentence_seconds": round(rows[0]["total"], 2),
        "per_sentence_seconds": round(sum(r["total"] for r in warm) / len(warm), 2),
        "tts_seconds": round(sum(r["tts"] for r in warm) / len(warm), 2),
        "rvc_seconds": round(sum(r["rvc"] for r in warm) / len(warm), 2),
        "real_time_factor": round(sum(r["total"] for r in warm) / audio, 3),
        "cpu_cores_busy": round(sum(r["cpu"] for r in warm) / sum(r["total"] for r in warm), 1),
        "rows": [{k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()} for r in rows],
    }
    if args.json:
        print(json.dumps(result))
        return
    print(f"settings: {result['settings']}")
    print(f"start (load models): {result['start_seconds']} s")
    print(f"first sentence after the start: {result['first_sentence_seconds']} s")
    print(f"per sentence afterwards: {result['per_sentence_seconds']} s (Kokoro {result['tts_seconds']} s, RVC {result['rvc_seconds']} s)")
    print(f"real time factor: {result['real_time_factor']} (below 1 = faster than speaking)")
    print(f"CPU: about {result['cpu_cores_busy']} cores busy while rendering")
    for r in result["rows"]:
        print(f"  {r['sentence']}: audio {r['audio']} s, rendered in {r['total']} s (Kokoro {r['tts']} s, RVC {r['rvc']} s, CPU {r['cpu']} s)")


if __name__ == "__main__":
    main()
