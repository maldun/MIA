# MIA as a service (podman compose)

Three containers: **mia** (this code, CPU only, Python 3.12), **ollama** (the language model, the only one that may use the GPU) and **searxng** (web search). Only MIA is published, on `127.0.0.1:8585`.

## Start

```
sudo dnf install podman-compose          # once; or docker with its compose plugin
deploy/up.sh                             # CPU      | deploy/up.sh rocm   (AMD)   | deploy/up.sh nvidia
deploy/up.sh down                        # stop (the volumes stay); deploy/up.sh logs -f mia
```

The first call writes `deploy/.env` (the SearXNG secret of this machine, not in git). MIA waits for Ollama and pulls `version` and `version_light` of the config through its API when they are missing (the first start downloads the models, the log says so).

## What is mounted

| in the container | from | why |
|---|---|---|
| `setup_cfg.json` | `deploy/setup_cfg.compose.json` (or `MIA_CONFIG`) | the config of the stack: `ollama_managed: false`, `ollama_host`, `searxng_url`, `sandbox_backend: none`, histories under `data/` |
| `data/` | volume `mia-data` | histories, presets, logs, token |
| `voice/models/kokoro/` | `voice/models/kokoro` (or `MIA_KOKORO_DIR`), read-only | the Kokoro model files (README of the main folder) |
| `ui/godot/build/web/` | `ui/godot/build/web` (or `MIA_CHARACTER_DIR`), read-only | the 3D character |
| Ollama's models | volume `ollama` | models are downloaded once |

## The 3D character

The character is not in the image or in git. Put the zip from your Drive in with one command:

```
deploy/up.sh character path/to/mia-character-web-1.zip
```

It copies the zip to `ui/character/`, checks it against `ui/character/manifest.json` (SHA-256, safe paths), unpacks it to `ui/godot/build/web` and recreates the MIA container so that it sees the new folder. Without the path it uses the zip that already lies in `ui/character/`. No Godot and no Blender are needed (`ui/character/README.md`).

## Settings in `.env` (all optional)

`MIA_PORT` (8585), `MIA_BIND` (127.0.0.1; `0.0.0.0` for other machines, then also set `public_hosts` in the config), `MIA_PROJECT` (mia; another name = a second stack next to the first), `MIA_CONFIG`, `MIA_KOKORO_DIR`, `MIA_CHARACTER_DIR`, `HSA_OVERRIDE_GFX_VERSION` (rocm, 11.0.0).

## Notes

- Not in the container on purpose: the script checks of the sandbox (`sandbox_backend: none`, bubblewrap and podman cannot run inside a container; the other hard checks work) and the https proxy (`https_port: null`; use a reverse proxy or Tailscale).
- Start at boot: `systemctl --user enable --now podman-restart.service` (the compose services have `restart: unless-stopped`) and `loginctl enable-linger $USER`.
- Tested 2026-10-21 with podman 5.7 and podman-compose, a throwaway stack with a tiny model: all three start, MIA pulls the model through the API, page and character are served, MIA reaches `searxng:8080` and `ollama:11434`, the character command works. The GPU files were not run (no change of the GPU setup while MIA was in use).
- Old containers of the same names (`ollama`, `mia-searxng` made by MIA's own start or `tools/searxng/run.sh`) use other names than the stack (`mia_ollama_1` ...), but both Ollamas cannot hold the GPU at the same time: stop one.
