# VRoid Character: Real-Time Expressions in Godot (Web)

## 1. Goal

Take an anime character exported from VRoid Studio (provided as a `.blend` file) and bring it into a Godot 4 project that:

- shows the character in a web browser, on any device, including phones;
- plays a library of reusable facial expressions with smooth transitions;
- lets the user create and save new expressions live with sliders;
- can generate new expressions from a text description using an LLM running on the user's own machine;
- **replaces the old video expressor of MIA** (pre-rendered `.mp4` clips per expression, see `expressor.py`/`web_app.py`): MIA's emotions and expressions now drive the 3D character (see 4.9).

Everything is hosted on one strong machine (the "host"). Remote devices only open a link.

## 2. Architecture overview

```
Remote device (browser)                    Host machine (strong GPU)
┌───────────────────────────┐              ┌──────────────────────────────────┐
│ Godot web export          │   HTTPS      │ Backend (small web server)       │
│  - renders the character  │ ───────────► │  - serves the Godot web export   │
│  - expression engine      │              │  - stores expression presets     │
│  - slider editor UI       │ ◄─────────── │  - proxies LLM requests          │
│  - LLM prompt UI          │   JSON       │            │                     │
└───────────────────────────┘              │            ▼                     │
                                           │ Local LLM server (e.g. Ollama)   │
                                           │  - bound to localhost only       │
                                           └──────────────────────────────────┘
        Remote access only through a private network (Tailscale). No public ports.
```

Key design decisions:

- **Rendering happens on the viewing device.** Only small JSON messages travel to the host.
- **The backend proxies all LLM calls.** The browser never talks to the LLM directly. This avoids CORS problems, keeps the LLM off the network, and allows swapping the LLM provider without touching the game.
- **Presets live on the host, not in the browser,** so all devices share the same expression library.

## 3. Inputs

- `.blend` file of the character, originally exported from VRoid Studio. Textures should be packed (File → External Data → Pack Resources). If they are not, report missing textures before continuing.
- MIA's existing configuration, which defines what the character must be able to express:
  - `emotion_map.json`: emotion keyword the LLM may answer with (`agree`, `disagree`, `neutral`, `annoyed`, `happy`, `MIA`) → expression key;
  - `expressions.json`: expression key (`greet`, `no`, `annoyed`, `talk`, `yes`, `idle`) → video, spoken text and voice clip. The voice clips stay, the videos are replaced by presets.
- No other assets are provided. Anything else must be created or sourced from open-licensed projects.

## 4. Functional requirements

### 4.1 Asset inspection (do this first)

- Open the `.blend` headless with Blender's Python API and produce `docs/asset_inventory.md` containing:
  - all meshes, with vertex counts;
  - all shape keys per mesh, grouped by prefix (VRoid typically uses names like `Fcl_EYE_*`, `Fcl_MTH_*`, `Fcl_BRW_*`, `Fcl_ALL_*`; confirm the actual names, do not assume);
  - armature and bone list, highlighting head, neck, jaw, and eye bones;
  - materials, shader setup, and texture images with resolutions;
  - whether VRM metadata or VRM expression definitions are present, and which VRM version (0.x or 1.0).
- Flag anything that may cause problems later: missing textures, unusual shaders, very high poly counts, duplicate shape-key names.

### 4.2 Export pipeline: Blender → Godot

- Export the character from Blender into a format Godot can import with expressions intact. Preferred route: VRM via the VRM Add-on for Blender, imported into Godot with the open-source `godot-vrm` add-on. Fallback: glTF/GLB with shape keys and armature.
- Make the export reproducible: a script (`tools/export_character.py`) that runs Blender headless and writes the exported file to the Godot project.
- After import, verify in Godot that every shape key from the inventory exists and can be driven.

### 4.3 Rendering

- Godot 4.x, **Compatibility renderer** (required for web export).
- Toon look matching the VRoid original: flat/stepped shading, outlines, correct eye and hair transparency.
- Test whether the MToon shader from `godot-vrm` works under the Compatibility renderer in a web build. If it doesn't, write a simplified toon shader that looks as close as possible, and document the differences.
- Simple scene: the character from roughly the waist up, neutral background, soft key light, and orbit/zoom camera controls (mouse and touch).

### 4.4 Expression engine

- An **expression** is a set of shape-key weights (0.0–1.0), optionally plus small bone offsets (jaw open, eye direction).
- Preset format (JSON, one file per preset or one library file, your choice; document it):

```json
{
  "name": "smug",
  "description": "confident half-smile, slightly lowered eyelids",
  "weights": { "Fcl_MTH_Fun": 0.6, "Fcl_EYE_Joy": 0.3 },
  "bones": { "jaw_open": 0.0 },
  "tags": ["happy", "confident"],
  "source": "manual"
}
```

- **Required presets** (14), named exactly so MIA's configuration can refer to them:
  - everything MIA already uses (one preset per key of `expressions.json`): `greet`, `no`, `annoyed`, `talk`, `yes`, `idle`;
  - the suggested starters: `neutral`, `happy`, `sad`, `angry`, `surprised`, `embarrassed`, `smug`, `thinking`.
  - The old videos only conveyed the mood; the presets keep that mood (e.g. `yes` = agreeing smile, `no` = stern, `annoyed` = half-lidded "Seriously?", `talk` = attentive, `idle` = friendly waiting face).
- **Gestures (arms, hands):** the arms hang relaxed by default. A gesture is a short keyframed arm and hand animation from `presets/gestures.json`
  (13 so far: wave, point, explain, shrug, think, hands_on_hips, hand_on_hip, arms_crossed, wave_off, hands_up, cheer, fist_pump, clasp).
  Limbs are authored as directions `[forward, up, outward]` with an optional `palm` direction (e.g. towards the viewer, or up); fingers use named poses
  (`relaxed`, `open`, `fist`, `point` = index finger out, rest in a fist). See `gesture_engine.gd`.
  A preset may name a gesture with `"gesture"`; playing the preset starts it. A gesture also names its facial `"expression"`, so playing a gesture on its own
  (e.g. from the menu) brings that face (cheer = happy). After the gesture's duration the arms ease back; "stop" returns them right away.
  Known limit: no collision with the jacket; the long sleeve cuffs hide most of the hands.
- **Speaking:** a preset with `"speaking": true` (`talk`) animates the mouth through random vowel shapes until another preset is played. A speech source can
  call `set_speaking()` for the same effect (real lip sync stays out of scope).
- **Background:** a custom background picture (png/jpg/webp) from the `backgrounds` folder of MIA, scaled to cover the view; plain colour if there is none.
  The server lists and delivers the pictures; the page or the menu can switch between them.
- **Camera:** default view shows the whole figure; named views `body`, `bust`, `face`; orbit/zoom with mouse and touch.
- `bones` supports `head_pitch`, `head_yaw`, `head_roll`, `eye_yaw`, `eye_pitch` (degrees). The model has no jaw bone, so mouth opening goes through the `Fcl_MTH_*` shape keys.
- `source` is one of `manual`, `llm`, `llm_edited`.
- Smooth blending between expressions with a configurable duration (default ~0.25 s) and easing.
- Shape keys not mentioned in a preset blend back to 0.
- **Automatic blinking** layered on top of any expression, with randomized intervals. Suppressed when the current expression already has closed eyes.
- **Subtle idle motion** (breathing, slight head sway) so the character never looks frozen.
- Validation: reject unknown shape-key names, clamp values to 0–1, and log what was corrected.

### 4.5 Expression editor (in-game UI)

- A panel listing every facial shape key with a slider, grouped by category (eyes, brows, mouth, other), with a search/filter field.
- Load any preset into the sliders, adjust, and see the result live.
- Save as a new preset (name, description, tags), overwrite, rename, delete.
- Reset to neutral.
- Must be usable on a phone: the panel can collapse, sliders are touch-friendly.
- Presets are saved to the backend (see 4.7).

### 4.6 LLM-generated expressions

- Text field: the user describes an expression ("surprised but trying to hide it").
- The game sends the description to the backend. The backend builds the prompt and calls the LLM.
- The prompt includes:
  - the full list of available shape-key names, with short explanations where the name isn't self-explanatory;
  - a selection of existing presets as examples, preferring those the user created or approved;
  - the required output format (JSON matching the preset schema), using the LLM server's structured/JSON output mode where available.
- The backend validates the response (schema, known keys, clamped values) and retries once on invalid output.
- **Latency hiding:** while waiting, the game immediately blends to the closest existing preset (by tags/description match, or ask the backend for a quick match), then blends to the LLM result when it arrives.
- After an LLM result is shown, the user can:
  - **Keep** → saved as a preset with `source: llm`;
  - **Edit** → opens it in the slider editor; on save, `source: llm_edited`;
  - **Reject** → discarded, but logged.
- All accepted, edited, and rejected results are logged (`data/feedback_log.jsonl`) so future prompts can use them as positive and negative examples.

> Decision for 4.7: the backend is MIA's existing Flask app (not a second FastAPI server): one server for page, character and presets,
> one set of access rules. The preset API is in `presets_api.py`; see ui/README.md, phase 6.

### 4.7 Backend (host machine)

- Small web server. Suggested: Python + FastAPI (any lightweight option is fine; justify the choice).
- Responsibilities:
  - serve the Godot web export as static files, with the correct MIME types (including `.wasm`);
  - REST API for presets: list, get, create, update, delete;
  - `POST /api/expression/generate`: description in, validated preset out;
  - `POST /api/expression/match`: description in, closest existing preset out (fast, no LLM required);
  - append to the feedback log.
- LLM provider is configurable: default is a local Ollama (or llama.cpp) server on `localhost`. Model name, server URL, timeout, and temperature live in a config file. The design should allow adding a cloud provider later behind the same interface.
- Presets and logs are stored as files on disk (JSON/JSONL); no database needed.

### 4.8 Web deployment and remote access

- Export Godot to Web. **GDScript only** (no C#).
- Prefer a **single-threaded** web export so the page works without special cross-origin isolation headers. If threads are required, configure the COOP/COEP headers on the backend and document why.
- Remote access through **Tailscale** only. Use Tailscale's HTTPS support (e.g. `tailscale serve`) so the page is served over HTTPS without opening public ports. Verify the exact commands at setup time and document them.
- Documented one-command start: start the LLM server (if not running), the backend, and the HTTPS exposure.

### 4.9 Integration with MIA (replaces the video expressor)

- MIA's chat page shows the Godot web export in place of the `<video>` element (embedded, same origin, e.g. `<iframe>`).
- `expressor.py`: a new `PresetExpressor` replaces `VideoExpressor`. `express(key)` no longer copies a video; it tells the UI to play the preset `key`. `web_app.express_and_reload()` keeps its signature and behaviour (including the voice clip via `VoiceExpressor`), and the video code, `video.mp4` copying and the `reload_video` events are removed.
- Transport MIA → UI: MIA emits an event over its existing Socket.IO connection (`expression`, payload `{name}`); the page forwards it to the Godot iframe (`postMessage`), where a small JavaScript bridge calls the central expression API. Until the backend of 4.7 exists, the presets are loaded from the Godot project; afterwards from the backend.
- `emotion_map.json` keeps its existing entries and gains one entry per new emotion the LLM may use: `sad`, `angry`, `surprised`, `embarrassed`, `smug`, `thinking` (each mapping to the preset of the same name). MIA's LLM prompt is built from this file, so the new emotions become available to the LLM automatically.
- `expressions.json` keeps `text` and `voice`; the `vid` entry becomes optional and unused. New expressions may have no voice clip yet (`VoiceExpressor` must then skip silently); clips can be generated later with `speak.py --generate`.
- Unknown preset names must not crash MIA: the UI logs them and keeps the current expression.
- Out of scope here: chat input and the chat page (modernized in `REQUIREMENTS_CHAT.md`), speech audio streaming and lip sync stay as they are.

## 5. Non-functional requirements

- **Performance:** smooth playback (target 30+ fps) on a mid-range phone browser, 60 fps on desktop.
- **Load size:** keep the initial download reasonable for mobile; compress textures where it doesn't visibly hurt quality, and report the final size.
- **Latency:** preset switching feels instant; LLM generation should normally complete within a few seconds on the host.
- **Robustness:** if the LLM is offline or slow, the game still works with presets and the editor, and shows a clear message.
- **Privacy:** nothing leaves the host machine and the private network unless a cloud LLM is explicitly configured.
- **Reproducibility:** a README that explains setup from scratch on the host: required software, versions, and every step to build and run.

## 6. Out of scope for now (possible later phases)

- Texture enhancement with image models.
- Body animation beyond idle motion (gestures, walk cycles, mocap).
- Dialogue-driven expressions (LLM tags each line of dialogue with an emotion).
- Vision feedback: a vision-capable model looks at a screenshot of the result and corrects the expression.
- Webcam face tracking.
- Lip sync.

Keep the code structured so these can be added without major rewrites (in particular: expressions are applied through one central API that any input source can call).

## 7. Suggested phases and acceptance criteria

| Phase | Deliverable | Done when |
|---|---|---|
| 1. Inspect | `docs/asset_inventory.md` | Every shape key, bone, material and texture is listed, and problems are flagged. |
| 2. Pipeline | Export script + character in Godot | The character renders in the Godot editor and every shape key can be driven. |
| 3. Web render | Web export served locally | The character renders with the toon look in desktop and phone browsers. |
| 4. Expressions | Expression engine + the 14 required presets (4.4) | Presets blend smoothly; blinking and idle motion work; all 14 look right in a contact sheet. |
| 5. MIA integration | `PresetExpressor`, iframe + event bridge, extended `emotion_map.json` (4.9) | MIA's answers drive the character; no video code is left. |
| 6. Editor | Slider panel + preset API | A new expression can be built on a phone, saved, and loaded on another device. |
| 7. Chat | Modern chat page around the character, see `REQUIREMENTS_CHAT.md` (its phases C1-C5) | A real conversation with MIA works in a modern chat UI on desktop and phone, with history, streaming and stop. |
| 8. LLM | Generate endpoint + UI | A text description produces a valid expression; keep/edit/reject works and is logged. **Built** (see ui/README.md, phase 8; the answers of a real model still need a try-out). |
| 9. Remote | Tailscale HTTPS setup + README | The page opens over HTTPS from a phone outside the home network. **Prepared, optional** (see ui/README.md, phase 9; not tried against a real Tailscale). |

After each phase, stop and report what was built, how to test it, and any decisions the user should make before the next phase.

## 8. Open questions for the user

Ask these before or during the relevant phase rather than assuming:

1. Host machine: operating system and GPU? *(answered: Fedora 43, RX 7800 XT)*
2. Which local LLM server is already installed, if any (Ollama, llama.cpp, LM Studio)? Preferred model? *(answered: Ollama in a podman container, light model `gemma4:12b-it-qat`)*
3. Godot version preference (default: latest stable 4.x)? *(answered: 4.6.1)*
4. Which starter expressions to create first (answered: the 14 of 4.4)
5. Should the editor be protected (e.g. a simple password), or is Tailscale access control enough?
