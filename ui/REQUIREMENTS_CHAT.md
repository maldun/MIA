# MIA Chat: a modern chat page around the 3D character

## 1. Goal

MIA's page should look and feel like a modern chat application, with the 3D character as the main visual:

- The character fills the whole window; the chat is a clean, translucent panel on top of it (a bottom sheet on phones).
- A real conversation view: message bubbles for you and for MIA, timestamps, formatted answers (markdown, code), answers that
  appear while MIA is still writing, a proper input field, and the history of earlier conversations.
- Works well on desktop and phone, in dark and light themes, with keyboard and screen reader.
- Everything stays on the host machine and the private network: no external scripts, fonts or services.

The chat stays HTML, CSS and JavaScript (decision: text input, text selection, the on-screen keyboard and markdown rendering are far
better in the browser than in Godot's web export). Godot keeps the character, the background and the expression editor.

## 2. Where we start

What exists today (`templates/index.html`, `web_app.py`), as facts:

- One page with a heading ("I am MIA, eager to help!"), the character iframe, an iframe with the **current answer only**, a plain
  textarea and a "Send Answer" button. There is no conversation view: no history, no bubbles of your own messages, no timestamps.
- The answer is written into a shared file (`answer.html`) on every streamed chunk and shown by reloading an iframe. All devices share
  that one file; it is rewritten from scratch for every chunk; the markdown is rendered by a web component (`md-block`).
- The socket handler of a message **blocks** until the whole exchange is finished (LLM, speech, pauses), so a second message or a
  second device has to wait, and there is no way to stop MIA.
- `socket.io` and `marked` are loaded from CDNs (needs internet; against the privacy goal).
- Commands (`/light!`, `/full!`, `/break!`, `/goodnight!`, `/dream!`, `/time!`) are typed blind; their result appears as an "answer".
- The LLM history (`memories.json`) is MIA's *memory*, not a chat log: it contains calibration prompts, hourly time updates
  ("Hi MIA it is ..."), summaries and correction messages ("penalties"), and it is replaced by a summary when MIA "dreams".
  Answers start with an emotion keyword line (`thinking`, `happy`, ...) that is filtered out before showing.
- Already working and to be kept: expression events (`expression`), the character handshake (`character_ready`), the `speaking`
  messages from the audio element, sentence-wise speech (`SpeechStreamer`), the HTTPS proxy, the allowed-origins rule.

Problems to solve: no conversation context, no history, no rich text, no streaming display per message, blocking server, no stop,
CDN dependencies, layout from an old grid (black areas, answer pane next to the character), poor phone usability, no accessibility.

## 3. Principles

1. **Chat in HTML.** Plain HTML, CSS and ES-module JavaScript, no build step and no UI framework. Small libraries are allowed if
   they are vendored (served from the host): a markdown parser, an HTML sanitizer, a code highlighter, the socket.io client.
2. **One source of truth for what is shown:** an append-only **chat log** on the server (new, see 6.2), separate from the LLM memory.
   All devices show the same conversation and update live.
3. **The server never blocks the page.** Exchanges run in a background task; the page always stays responsive.
4. **The character is the stage.** The character is full-window; the chat overlays it and the camera frames the character in the free area.
5. **Design tokens.** All colors, sizes, radii, shadows and fonts are CSS variables; themes only change variables.
6. **Progressive and robust.** Missing pieces degrade gracefully (character not loaded, server offline, no backdrop-filter support).
7. **No secrets in the page, no external requests, no inline scripts** (a strict Content-Security-Policy is part of the work).

## 4. Layout and look

### 4.1 Layouts

```
Wide screen (>= 900 px)                     Phone, portrait
+-----------------------------+----------+   +--------------------+
|  character (full window)    | header   |   |                    |
|                             |----------|   |  character         |
|        (camera frames the   | messages |   |  (upper 40-50 %)   |
|         free left area)     |   ...    |   |                    |
|                             |----------|   |-- drag handle -----|
|                             | composer |   | messages           |
+-----------------------------+----------+   | composer (sticky)  |
                                             +--------------------+
```

- **Wide:** chat panel at the right (default 420 px, 360-640 px, resizable by dragging the edge, remembered per device), rounded
  corners, translucent "glass" (blur behind it, with a solid fallback). It can be collapsed to a thin button; then only the
  character is visible and the last answer shows briefly as a **caption** at the bottom of the character area.
- **Phone / narrow:** bottom sheet with three snap heights: peek (composer + last message), half, full. A drag handle changes them;
  the composer stays above the on-screen keyboard (uses the visual viewport and safe-area insets), the character stays visible above.
- **Landscape phone:** panel at the right like wide screens, 45 % width.
- **Header** (inside the panel): MIA's name and avatar, a status line ("online", "thinking...", "speaking...", "offline"), and a menu button.
  The menu has: Character (view: body, bust, face), Background, Expression editor, Sound (mute, volume), Theme, Settings, About.
- The old heading, the answer iframe and the grid are removed.

### 4.2 Visual design

- Modern messenger look: bubbles with rounded corners, tails or grouping, soft shadows, clear hierarchy, generous spacing, one accent color
  (default: the blue of the character's hair), subtle motion.
- **Themes:** dark (default), light, and "system". Contrast at least WCAG AA in both. The accent is a setting with 4-6 presets.
- **Typography:** the system font stack by default (no downloads). Message text 16 px minimum on phones (also avoids zoom-on-focus on iOS),
  code in a monospace stack. Line length of messages limited for readability.
- **Motion:** short fades and slides (150-250 ms), a typing indicator (three dots) while MIA is thinking, a gentle caret while streaming.
  `prefers-reduced-motion` turns animation off.
- **Icons:** inline SVG (vendored, no icon font, no CDN).
- Empty state: a friendly first message with a few suggestions ("Say hello", "What can you do?") that fill the composer.

## 5. Chat features

### 5.1 Messages

- **Bubbles** for you (right, accent color) and MIA (left, neutral), with sender name/avatar on the first message of a group, timestamps
  (relative, full date and time in a tooltip and for screen readers), day separators ("Today", "Yesterday", date).
- **Markdown** for MIA's messages: paragraphs, emphasis, headings, lists, task lists, blockquotes, tables, horizontal rules, inline and
  fenced **code** (language label, **copy** button, syntax highlighting, horizontal scroll, never overflowing the bubble), links (open in a
  new tab with `rel="noopener noreferrer"`), images only from the same origin (no remote images). All HTML is sanitized (allow list).
  Your own messages are shown as typed (preserved line breaks, links made clickable), not as markdown.
- **Streaming:** a message grows while MIA writes; the typing indicator is shown from sending until the first text arrives; updates are
  batched per animation frame (no flicker, no layout jumps; markdown re-rendered incrementally or at the end of each block).
- **Emotion:** MIA's emotion for a message (from the keyword line the LLM sends) is shown as a small badge or emoji next to the name;
  the keyword line itself is never shown. Several emotions in one answer: the last one is shown, all are kept in the log.
- **Message actions** (on hover/long press): copy text, copy as markdown. Later (optional): speak again, regenerate the last answer.
- **Status of your messages:** sending, sent, failed (with a retry button). Failed means: not delivered to the server.
- **System notes:** small centered lines for events that are not conversation: model switched, MIA is dreaming, reconnected, errors
  (LLM offline, speech offline). Corrections the server sends to the LLM ("penalties") are **not** shown as your messages; at most
  a collapsed note ("MIA was reminded to start with an emotion").
- **MIA's own messages** (the hourly time check, reminders) appear as normal MIA messages with a small "automatic" marker.

### 5.2 Composer

- Auto-growing textarea (1 to 8 lines, then scrolls), placeholder, send button (disabled while empty), **Enter sends, Shift+Enter
  newline** on desktop; on phones Enter inserts a newline and the send button sends (setting). Never sends while an IME composition is active.
- A **stop** button replaces send while MIA is answering (stops the answer; the part already received stays, marked as stopped).
- While MIA is busy a new message is queued (one place, shown as "waiting") or refused with a hint; behavior is a setting, default: queue one.
- **Slash commands:** typing `/` opens a list of the commands with a short description (`/light!` small model, `/full!` large model,
  `/dream!` summarize memory, `/goodnight!` dream and shut down, `/break!` shut down, `/time!` send the time to MIA), filtered while typing,
  selectable with arrows/Enter/tap. Commands appear in the conversation as system notes, not as chat bubbles. Dangerous ones
  (`/break!`, `/goodnight!`) ask for confirmation.
- **Draft** per device is kept (localStorage) until sent. Maximum message length 8000 characters with a counter near the limit.
- Autofocus on wide screens, not on phones (no keyboard popping up on load). Up arrow in an empty composer recalls the last message.

### 5.3 History and navigation

- On load the last 50 messages are shown, scrolled to the bottom. Scrolling up loads older ones (pages of 50) until the start of the log.
- **Autoscroll:** follows new text only while the reader is at the bottom; if scrolled up, a "new messages" button appears
  (with an unread count) that jumps to the latest.
- Long conversations stay fast: at most about 300 messages in the DOM (older ones are removed from the top and reloaded on demand).
- Conversation is shared live between devices: a message sent on the phone appears on the desktop and the other way round.
- Optional: search in the conversation; export as markdown (menu).
- "Clear conversation" hides the history on this device or deletes the log (two different, clearly labelled actions, both confirmed).

### 5.4 Status and connection

- Connection indicator: "reconnecting ..." banner (not blocking), sending disabled while offline, drafts kept, automatic retry with backoff.
- Server status in the header: online/offline, current model (large/light), busy (thinking, speaking). Errors from the LLM or speech
  are shown as system notes with a short, human message (details in the log).

### 5.5 Sound

- Speech playback stays as it is (the page plays the audio files MIA produces); controls: mute toggle and volume in the menu,
  a speaker icon on the message that is being spoken; the character's mouth keeps following `speaking` messages.
- Browsers block autoplay until the first interaction: the page shows a one-time "tap to enable sound" hint instead of failing silently.

## 6. Backend

### 6.1 Principle

The server describes the conversation as **messages** and pushes changes over the existing socket.io connection; the page renders them.
The old way (rewriting `answer.html`, reloading an iframe, the `answer` event) is removed. During the migration the old `message`
event keeps working until the new page is complete.

### 6.2 Chat log (new)

- Append-only JSON lines file, `data/chat_log.jsonl` (setting `chat_log`; not in version control), one record per visible message:
  `{"id": "...", "role": "user|assistant|system", "text": "...", "markdown": true, "emotion": "happy", "auto": false,
  "created": "2026-10-18T10:00:00Z", "status": "done|stopped|error", "model": "gemma4:12b-it-qat"}`.
  Ids are sortable (time based). Streaming messages are written when they are finished (or stopped/failed).
- Independent of `memories.json`: dreaming and summaries do not touch it. Calibration prompts, hourly time prompts to the LLM,
  summaries and penalties are not chat messages and are never written to it.
- Size is bounded: rotation or a configurable maximum (default 10000 messages, oldest dropped); the file is written atomically per line.
- Retention and privacy: the log stays on the host; deleting it (menu) removes the file content; documented in the README.

### 6.3 Events and API

Socket.IO (names versioned in one place, documented):

| Direction | Event | Payload |
|---|---|---|
| client -> server | `chat_send` | `{id (client id), text}`: ack with the stored message or an error |
| client -> server | `chat_stop` | `{}`: stops the running answer |
| server -> all | `chat_message` | the complete message (your message with server time, system notes, automatic MIA messages) |
| server -> all | `chat_start` | `{id, role: "assistant", created}`: MIA starts a message (typing indicator) |
| server -> all | `chat_delta` | `{id, text}`: the filtered text so far (cumulative, so a late client can catch up) |
| server -> all | `chat_done` | `{id, text, emotion, status}` |
| server -> all | `chat_status` | `{busy, activity: "idle|thinking|speaking", model, profile, queue}` |
| server -> all | `chat_error` | `{id?, message}` human readable |

REST:

- `GET /api/chat/history?before=<id>&limit=50` visible messages, newest last; `GET /api/chat/status`.
- `POST /api/chat/clear` with `{"scope": "log"}` (needs the editor token or a `chat_token`; the page confirms first).
- Existing: expression events, `character_ready`, `speaking` stay as they are.

### 6.4 Processing

- `chat_send` is acknowledged immediately; the exchange runs in a background task (thread or socket.io background task), one at a time;
  a second message waits in a queue of length 1 (configurable). The socket handler never sleeps or waits for speech.
- **Stop:** closes the stream to Ollama, keeps the text received so far, records the message as `stopped`, and lets the speech stream finish
  the current sentence or stops it too (setting).
- Streaming deltas are throttled (at most about 20 per second per message).
- Emotion keywords, expressions, speech streaming, penalties and the time check keep working through the same path; their
  visible results become messages or system notes as described in 5.1.
- Input validation: text length, control characters stripped, commands recognized server-side as before (same list as the palette,
  served by `GET /api/chat/commands` so page and server never disagree).
- Security: sanitized rendering on the client; the server stores text only (no HTML); same-origin and allowed-origin rules as for
  the presets; a Content-Security-Policy that allows only own scripts and styles; rate limit per connection (for example 10 messages
  per minute) against accidents.

## 7. Character integration

- The character iframe is `position: fixed; inset: 0` behind the UI; the panel sits above it; areas not covered by the panel pass
  mouse and touch to the character (camera orbit, zoom).
- **Free-area framing:** the page tells the character how much of the window the panel covers (`{"type": "viewport_inset", left, right, top, bottom}`);
  the camera shifts so the character is centered in the free area, with smooth animation when the panel is resized, collapsed or the
  sheet snaps. New bridge message, implemented in `host_bridge.gd`, with tests.
- **Caption mode:** when the chat is collapsed, MIA's current answer appears as a caption at the bottom of the character area and fades out.
- Menu entries for camera view, background picture and the expression editor call the existing bridge/messages
  (`background`, `view` (new), editor link).
- The character stays optional: if it cannot load (no WebGL, no build), the chat works full-width and shows a small notice.

## 8. Settings and persistence (per device, localStorage, all wrapped in try/catch)

Theme (dark/light/system), accent color, panel width, sheet snap height, send-on-Enter, queue behavior, sound (mute, volume), show emotions,
show timestamps, compact mode (denser spacing). A "reset settings" action. Drafts and unsent messages are per device.

## 9. Accessibility and languages

- Full keyboard use: tab order, visible focus, shortcuts (focus composer, collapse panel, scroll to latest, open menu), Esc closes layers.
- Semantics: message list as `role="log"` with polite live updates that announce a finished message (not every streamed token);
  buttons have labels; status changes are announced; colors are never the only signal.
- Targets of at least 44 x 44 px for touch; text zoom to 200 % without loss; `prefers-reduced-motion` and `prefers-contrast` respected.
- All UI texts come from one dictionary file (English now, German prepared); dates and numbers follow the browser locale.

## 10. Non-functional requirements

- **Performance:** first meaningful paint of the chat under 1 s on the home network (the character loads independently); JavaScript of the
  chat itself (without vendored libraries) under 100 KB gzipped; 60 fps while scrolling 300 messages and while streaming; no layout shift
  from streaming text.
- **Browsers:** current Chrome, Firefox, Safari (iOS 16+), Android Chrome; widths from 320 to 2560 px.
- **Offline of dependencies:** nothing is loaded from the internet; all libraries are served by MIA with fixed versions (and a note of
  their licenses).
- **Robustness:** every network and storage access can fail without breaking the page; the page never loses a typed draft.
- **Maintainability:** modules by feature (state, socket client, renderer, composer, layout, settings), documented events, no global state
  on `window` except a debug handle.

## 11. Testing

- **JavaScript unit tests** with Node's built-in test runner (`node --test`, Node 22 is installed): markdown rendering and sanitizing
  (including attack strings), message grouping and day separators, streaming merge, autoscroll rules, command palette filtering,
  settings storage with a failing localStorage, i18n lookup.
- **Python tests:** chat log (append, paging, rotation, atomic writes, corrupt line handling), event flow with the socket.io test client
  (send, stream, done, stop, queue, errors, two clients see the same), history filtering (no calibration/time/summary/penalty messages),
  commands list, rate limit, validation.
- **Browser tests:** headless Chromium driven through the protocol (`ui/tools/browser_check.py`, extended with clicks, typing and
  viewport changes): send a message with a stub LLM, see it stream, stop it, reload and see the history, collapse and resize the panel,
  phone viewport snapping, keyboard-only use. Screenshots at 360x740, 768x1024 and 1440x900 in dark and light theme are compared by eye in
  the review of each phase (and stored with the reports).
- **Manual checklist on a real phone** (iOS and Android): keyboard behavior, sheet dragging, long press actions, autoplay hint, HTTPS warning flow.
- A **stub LLM** for tests (a small fake Ollama client) so no model is needed.

## 12. Phases and acceptance

| Phase | Deliverable | Done when |
|---|---|---|
| C1 Foundation | Layout shell (full-window character, panel / bottom sheet, header, menu), design tokens, themes, vendored libraries, strict CSP, i18n skeleton | The new page loads without any external request, looks right in dark and light on three viewports, the old page parts are gone, the character works as before. |
| C2 Backend | Chat log, message model, `chat_*` events, background processing, queue, stop, history API, commands API | A script or test client can send, stream, stop and read the history; two clients see the same; the old blocking handler is gone; tests green. |
| C3 Chat | Bubbles, markdown, streaming, typing indicator, composer, command palette, autoscroll, history paging, status and reconnect | A real conversation with MIA works end to end on desktop and phone viewports, including stop, reload and history. |
| C4 Character | `viewport_inset` framing, caption mode, menu entries (view, background, editor, sound) | The character is centered in the free area while the panel opens, closes, resizes and snaps; collapsing shows captions. |
| C5 Polish | Accessibility pass, reduced motion, performance budget, settings, empty state, cleanup of old code (`answer.html`, `md-block`, CDN links), documentation | Checklist of section 9 and 10 passes, README updated, manual phone checklist done. |
| C6 Optional | Regenerate, speak again, search, export, accent presets, German texts | Chosen after C5. |

After each phase: stop, report what was built, how to test it, and what to decide next.

## 13. Out of scope for now

Voice input (microphone), attachments and images from the user, accounts and multiple users, message editing, push notifications, an
installable app / offline mode (a self-signed certificate prevents service workers), chat rendered inside Godot, translating MIA's answers.

## 14. Open questions

Suggested answers are in brackets; the work starts with these unless you decide otherwise.

1. Chat panel at the **right** on wide screens, or on the left, or floating? [right]
2. Default theme and accent: dark with the blue of the character's hair? [yes]
3. Show MIA's emotion as a badge/emoji on each message? [yes, small, can be switched off]
4. Keep the whole conversation visible forever (a separate chat log), independent of MIA's memory? [yes; deletable from the menu]
5. Should the hourly "time check" messages from MIA be visible? [yes, marked "automatic", hideable]
6. Enter sends on phones, or Enter = new line? [new line, send button sends]
7. While MIA is busy: queue one message, or block the composer? [queue one]
8. Should sending messages need a token (like the expression editor), or is the home network enough? [no token now; optional `chat_token` later, needed once MIA is reachable from outside]
9. English only for the interface now? [yes, German texts prepared in the dictionary]
10. Is "stop" while MIA is speaking supposed to stop the speech too? [yes, setting]
