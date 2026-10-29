# MIA as a service (podman compose)

Four containers: **mia** (this code, CPU only, Python 3.12), **https** (Caddy, TLS in front of MIA), **ollama** (the language model, the only one that may use the GPU) and **searxng** (web search). Published are `http://127.0.0.1:8585` (MIA) and `https://127.0.0.1:8586` (same page through Caddy).

## Start

```
sudo dnf install podman-compose          # once; or docker with its compose plugin
deploy/up.sh                             # CPU      | deploy/up.sh rocm   (AMD)   | deploy/up.sh nvidia
deploy/up.sh down                        # stop (the volumes stay); deploy/up.sh logs -f mia
```

The first call writes `deploy/.env` (the SearXNG secret of this machine, not in git). MIA waits for Ollama and pulls `version` and `version_light` of the config through its API when they are missing (the first start downloads the models, the log says so).

## HTTPS

Browsers run the 3D character only in a secure context: `http://localhost:8585` is one, a LAN address needs HTTPS. The `https` service (`deploy/Caddyfile`) answers on port 8586 for any name or address with a certificate of its own local CA, so on another device the browser warns once ("not secure", continue). To get rid of the warning, trust the CA once on each device:

```
podman cp mia_https_1:/data/caddy/pki/authorities/local/root.crt mia-ca.crt     # then import it as trusted certificate authority
```

For other devices set `MIA_BIND=0.0.0.0` in `deploy/.env` and open `https://<address of this machine>:8586`. If MIA refuses the page (origin), add the name you use to `public_hosts` in the config. The CA lives in the volume `caddy-data`, so the certificates stay the same after a restart.

## What is mounted

| in the container | from | why |
|---|---|---|
| `setup_cfg.json` | `deploy/setup_cfg.compose.json` (or `MIA_CONFIG`) | the config of the stack: `ollama_managed: false`, `ollama_host`, `searxng_url`, `sandbox_backend: none`, histories under `data/` |
| `setup_cfg.local.json` | `deploy/setup_cfg.local.json` | the settings of this machine (the login ...), laid over the config above key by key; not in git, made by `up.sh` as `{}` |
| `data/` | volume `mia-data` | histories, presets, logs, token |
| `voice/models/kokoro/` | `voice/models/kokoro` (or `MIA_KOKORO_DIR`), read-only | the Kokoro model files (README of the main folder) |
| `ui/godot/build/web/` | `ui/godot/build/web` (or `MIA_CHARACTER_DIR`), read-only | the 3D character |
| `backgrounds/` | `backgrounds` (or `MIA_BACKGROUND_DIR`), read-only | the pictures behind the character (`backgrounds/README.md`); a new picture appears when the page is reloaded |
| Ollama's models | volume `ollama` | models are downloaded once |

## The personality (calibration.txt)

`calibration.txt` (how MIA addresses you, her character) is your own file and not in git, so the container starts without it. Copy it into the data volume once, and again after you change it:

```
deploy/up.sh calibration                 # uses calibration.txt of the MIA folder
deploy/up.sh calibration path/to/file    # another file
```

MIA is restarted; the file stays in the volume `mia-data`.

Her memories (`memories.json`, `long_time_history.json`) of an old installation are not in the volume either. Take them over with

```
deploy/up.sh memories                    # from the MIA folder
deploy/up.sh memories path/to/folder
```

MIA is stopped first (it saves its history when it stops), the files are copied in and MIA starts again. What the container had before is kept as `<name>.container-previous` in the volume.

## The login (password check)

Off by default. Turn it on and make the owner account:

```
deploy/up.sh owner NAME                  # asks for the password twice (at least 8 characters); never an argument
```

The command also turns the login on, in `deploy/setup_cfg.local.json`; an account that exists already is kept (it is not created twice). To switch the password check alone, without a container: `deploy/up.sh login on|off|status` (`on` warns when no account exists yet, because you could not log in then). That file holds the settings of **this machine**, is not in git and is laid over the tracked `deploy/setup_cfg.compose.json` key by key (do not edit the tracked file for your machine). Restart MIA to apply it:

```
deploy/up.sh db up -d --no-deps --force-recreate mia      # without "db" if the stack runs without the database
```

The page then asks for the login. **In the stack log in over HTTPS: `https://localhost:8586`** (the browser asks once about the certificate of the local CA). MIA sees every connection from the podman network and not as `127.0.0.1`, so a password over plain HTTP (`http://localhost:8585`) is refused; the `https` service is named in `trusted_proxies` of `setup_cfg.compose.json`, which is why its HTTPS counts. A MIA that runs outside the stack still accepts a password from `localhost` over HTTP. From other devices use `https://<address>:8586`. Five wrong logins in a minute lock the account for a minute. The accounts live in the data volume (`data/db`), so they survive a rebuild. More accounts and a new password: `podman exec -it mia_mia_1 python /opt/mia/MIA/tools/accounts_cli.py create|password|list NAME --dir /opt/mia/MIA/data/db`; users change their own password on the page.

## Taking over an old installation

The settings you made in the app (expression presets, gestures), the chat log and the editor token are files in the `data/` folder of the old installation; the container starts with an empty volume. In one go:

```
deploy/up.sh data                  # presets, gestures, chat_log.jsonl, feedback_log.jsonl, editor_token.txt from <MIA folder>/data
deploy/up.sh calibration           # how she addresses you
deploy/up.sh memories              # her conversation memory
```

Each command stops MIA while it copies and starts it again. Reload the page afterwards; the editor of the character shows the presets again.

## Backup and restore

```
deploy/up.sh backup                      # mia-backup-<date>.tar.gz in the current folder
deploy/up.sh backup path/to/file.tar.gz
deploy/up.sh restore path/to/file.tar.gz
```

The archive holds the whole data volume: histories, chat log, presets, gestures, calibration, tokens, library index. MIA is stopped while the files are copied (it saves its history when it stops) and starts again. `restore` first saves the current state as `mia-before-restore-<time>.tar.gz`, so a wrong restore can be undone with another restore. Files that exist only in the volume are not deleted by a restore. The models of Ollama (volume `ollama`) and the character are not part of it (they come from the downloads and the zip).

## The 3D character

The character is not in the image or in git. Put the zip from your Drive in with one command:

```
deploy/up.sh character path/to/mia-character-web-1.zip
```

It copies the zip to `ui/character/`, checks it against `ui/character/manifest.json` (SHA-256, safe paths), unpacks it to `ui/godot/build/web` and recreates the MIA container so that it sees the new folder. Without the path it uses the zip that already lies in `ui/character/`. No Godot and no Blender are needed (`ui/character/README.md`).

## An Ollama that exists already

Put its address in `deploy/.env`, e.g. on another machine:

```
OLLAMA_URL=http://192.168.1.50:11434
```

`deploy/up.sh` then does not start the `ollama` service at all and MIA talks to that address (the environment variable `MIA_OLLAMA_HOST` overrides `ollama_host` of the config; the same works outside compose). The GPU files are not needed then, the GPU belongs to that machine. The other Ollama must be reachable from the container (on the other machine `OLLAMA_HOST=0.0.0.0` and an open port; Ollama has no login, so keep it inside your own network or a VPN). MIA pulls `version` and `version_light` there if they are missing; set `"ollama_pull": false` in the config to leave that Ollama's models alone. For an Ollama on the same machine use the address of the host (`http://host.containers.internal:11434` in podman) instead of `localhost`.

## Settings in `.env` (all optional)

`OLLAMA_URL` (see above), `MIA_PORT` (8585), `MIA_HTTPS_PORT` (8586), `MIA_BIND` (127.0.0.1; `0.0.0.0` for other machines, then also set `public_hosts` in the config), `MIA_PROJECT` (mia; another name = a second stack next to the first), `MIA_CONFIG`, `MIA_KOKORO_DIR`, `MIA_CHARACTER_DIR`, `MIA_BACKGROUND_DIR`, `HSA_OVERRIDE_GFX_VERSION` (rocm, 11.0.0).

## Notes

- Not in the container on purpose: the script checks of the sandbox (`sandbox_backend: none`, bubblewrap and podman cannot run inside a container; the other hard checks work) and the https proxy (`https_port: null`; use a reverse proxy or Tailscale).
- Start at boot: `systemctl --user enable --now podman-restart.service` (the compose services have `restart: unless-stopped`) and `loginctl enable-linger $USER`.
- Tested 2026-10-21 with podman 5.7 and podman-compose, a throwaway stack with a tiny model: all three start, MIA pulls the model through the API, page and character are served, MIA reaches `searxng:8080` and `ollama:11434`, the character command works. The GPU files were not run (no change of the GPU setup while MIA was in use).
- Old containers of the same names (`ollama`, `mia-searxng` made by MIA's own start or `tools/searxng/run.sh`) use other names than the stack (`mia_ollama_1` ...), but both Ollamas cannot hold the GPU at the same time: stop one.
