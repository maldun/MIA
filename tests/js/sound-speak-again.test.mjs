// Speak again right after a stop (N-1.3, REQ-VPB-006, A-132 TD-11): TC-VPB-006 on the real sound.js with a fake clock and a fake audio element
// (TR-VOICE-005). node --test "tests/js/sound-speak-again.test.mjs"
// Markers: `// mark.req(...)` above a test, as in the other suites of this folder.
import test from 'node:test';
import assert from 'node:assert/strict';
import { initSound, STOP_DROP_MS } from '../../templates/static/chat/sound.js';

const flush = () => new Promise((resolve) => setImmediate(resolve));

/** an audio element that starts every line at once and records the url it was given */
function fakeAudio() {
  const listeners = {};
  return {
    src: '', muted: false, volume: 1, playing: false, started: [],
    addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
    removeAttribute() { this.src = ''; },
    pause() { this.playing = false; },
    async play() { this.playing = true; this.started.push(this.src); },
  };
}

function element() {
  const listeners = {};
  return { hidden: true, value: '', textContent: '', setAttribute() {}, addEventListener(name, fn) { (listeners[name] ||= []).push(fn); } };
}

/** the page of initSound on fakes; the clock is the fake one and a test moves it by hand */
function page() {
  const handlers = {};
  const socket = { id: 'me', on(name, fn) { handlers[name] = fn; }, emit() {} };
  const storage = { get: (key, fallback) => fallback, set() {} };
  const win = { setInterval: () => 1, clearInterval: () => {}, addEventListener: () => {}, console: { warn: () => {} } };
  globalThis.document = { visibilityState: 'visible', addEventListener: () => {} };
  const audio = fakeAudio();
  const time = { now: 50000 };
  const sound = initSound({
    audio, socket, character: { speaking: () => {} }, storage,
    muteToggle: element(), muteLabel: element(), muteIcon: element(), volume: element(), hint: element(),
    t: (key) => key, win, clock: () => time.now,
  });
  return { audio, sound, time, server: (name, data) => handlers[name]?.(data) };
}

// mark.req("REQ-VPB-006")
test('TC-VPB-006: speak again 1 s after a stop: the line that follows is enqueued and played', async () => {
  // Given the voice player with a clock, a Stop pressed 1 s ago (the window of STOP_DROP_MS = 3000 ms is still open)
  const p = page();
  p.sound.stop();
  p.time.now += 1000;
  assert.ok(1000 < STOP_DROP_MS);
  // When the user asks to speak an answer again and an audio_reload arrives
  p.sound.speakAgain();
  p.server('audio_reload', { url: '/audio/line-000007.wav', serial: 7 });
  await flush();
  // Then the line is enqueued: the audio element was given its url
  assert.deepEqual(p.audio.started, ['/audio/line-000007.wav']);
});

// mark.req("REQ-VPB-006")
test('TC-VPB-006: without the request a line 1 s after a stop is still dropped, as before', async () => {
  // Given the voice player with a clock, a Stop pressed 1 s ago
  const p = page();
  p.sound.stop();
  p.time.now += 1000;
  // When no request is made and an audio_reload arrives
  p.server('audio_reload', { url: '/audio/line-000008.wav', serial: 8 });
  await flush();
  // Then the line is dropped: late lines of the stopped answer stay out (REQ-VPB-002)
  assert.deepEqual(p.audio.started, []);
});
