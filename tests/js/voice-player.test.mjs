// The voice player (N-1.3, IF-112): TC-VPB-001 to TC-VPB-003 on a fake audio element. node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { VoicePlayer, CLAIM_EVERY_MS, initSound } from '../../templates/static/chat/sound.js';

/** an audio element that plays one line at a time and tells when two overlap */
function fakeAudio() {
  const listeners = {};
  const audio = {
    src: '', muted: false, volume: 1, playing: false, overlaps: 0, started: [], blockNext: false, failNext: false,
    addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
    removeAttribute() { this.src = ''; },
    pause() { this.playing = false; },
    async play() {
      if (this.blockNext) { const e = new Error('blocked'); e.name = 'NotAllowedError'; throw e; }
      if (this.failNext) { this.failNext = false; throw new Error('file gone'); }
      if (this.playing) this.overlaps += 1;
      this.playing = true;
      this.started.push({ url: this.src, audible: !this.muted });
    },
    finish() { this.playing = false; (listeners.ended || []).forEach((f) => f()); },
    breaks() { this.playing = false; (listeners.error || []).forEach((f) => f()); },
  };
  return audio;
}

/**
 * an audio element that settles play() as the HTML spec does (F1 of the verification): loading takes a task; a missing file fires
 * `error` and then rejects the play() promises pending at the failure with NotSupportedError; pause() and a new src reject a
 * pending play() with AbortError
 */
function specAudio(missing = []) {
  const listeners = {};
  let pending = [];
  let src = '';
  const fire = (name) => (listeners[name] || []).forEach((f) => f());
  const take = () => { const taken = pending; pending = []; return taken; };
  const refuse = (taken, name) => taken.forEach(({ reject }) => { const e = new Error(name); e.name = name; reject(e); });
  return {
    muted: false, volume: 1, playing: false, overlaps: 0, started: [],
    get src() { return src; },
    set src(value) { refuse(take(), 'AbortError'); src = value; this.playing = false; },
    addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
    removeAttribute() { src = ''; },
    pause() { refuse(take(), 'AbortError'); this.playing = false; },
    play() {
      const url = src;
      const started = new Promise((resolve, reject) => pending.push({ resolve, reject }));
      setImmediate(() => {
        if (url !== src || !pending.length) return;                       // aborted by pause() or a new src
        const taken = take();
        if (missing.includes(url)) { fire('error'); refuse(taken, 'NotSupportedError'); return; }
        if (this.playing) this.overlaps += 1;
        this.playing = true;
        this.started.push({ url, audible: !this.muted });
        taken.forEach(({ resolve }) => resolve());
      });
      return started;
    },
    finish() { this.playing = false; fire('ended'); },
  };
}

const line = (id, extra = {}) => ({ id, url: `/audio/${id}.wav`, serial: 1, ...extra });
const ids = (audio) => audio.started.map((s) => s.url.match(/\/audio\/(.*)\.wav/)[1]);
const flush = () => new Promise((resolve) => setImmediate(resolve));

function make(extra = {}) {
  const audio = fakeAudio();
  const player = new VoicePlayer({ audio, ...extra });
  const speaking = [];
  player.onSpeaking((value) => speaking.push(value));
  return { audio, player, speaking };
}

test('TC-VPB-001: five lines play in the order they arrive and never overlap', async () => {
  const { audio, player, speaking } = make();
  ['a', 'b', 'c', 'd', 'e'].forEach((id) => player.enqueue(line(id)));
  await flush();
  for (let n = 0; n < 5; n += 1) { audio.finish(); await flush(); }
  assert.deepEqual(ids(audio), ['a', 'b', 'c', 'd', 'e']);
  assert.equal(audio.overlaps, 0);
  assert.deepEqual(speaking, [true, false]);
});

test('TC-VPB-001: a line that arrives while another plays waits for it', async () => {
  const { audio, player } = make();
  player.enqueue(line('a'));
  await flush();
  player.enqueue(line('b'));
  await flush();
  assert.deepEqual(ids(audio), ['a']);
  audio.finish(); await flush();
  assert.deepEqual(ids(audio), ['a', 'b']);
});

test('TC-VPB-001: the end of a line is reported with the line, so the server can follow the serial', async () => {
  const ended = [];
  const { audio, player } = make({ onEnded: (l) => ended.push(l.serial) });
  player.enqueue(line('a', { serial: 7 }));
  await flush();
  audio.finish(); await flush();
  assert.deepEqual(ended, [7]);
});

test('TC-VPB-002: a muted device plays no sound and a second device still does', async () => {
  const one = make();
  const two = make();
  one.player.mute(true);
  one.player.enqueue(line('a')); two.player.enqueue(line('a'));
  await flush();
  assert.equal(one.audio.muted, true);
  assert.deepEqual(one.audio.started.filter((s) => s.audible), []);
  assert.deepEqual(two.audio.started.filter((s) => s.audible).length, 1);
  one.player.mute(false);
  assert.equal(one.audio.muted, false);
});

test('TC-VPB-002: stop ends the playing line, clears the queue and ends speaking', async () => {
  const { audio, player, speaking } = make();
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id)));
  await flush();
  player.stop();
  await flush();
  assert.equal(audio.playing, false);
  assert.deepEqual(ids(audio), ['a']);
  assert.equal(speaking.at(-1), false);
  assert.equal(player.queued, 0);
});

test('TC-VPB-002: a page that is not the owner of the voice stays silent', async () => {
  const { audio, player } = make();
  player.setOwner(false);
  player.enqueue(line('a'));
  await flush();
  assert.deepEqual(audio.started, []);
  player.setOwner(true);
  player.enqueue(line('b'));
  await flush();
  assert.deepEqual(ids(audio), ['b']);
});

test('TC-VPB-002: losing the voice while a line plays stops it and drops the queue', async () => {
  const { audio, player } = make();
  player.enqueue(line('a')); player.enqueue(line('b'));
  await flush();
  player.setOwner(false);
  assert.equal(audio.playing, false);
  assert.equal(player.queued, 0);
});

test('TC-VPB-003: a line that cannot be loaded is reported once and the next one plays', async () => {
  const failed = [];
  const { audio, player } = make();
  player.onLineError = (id) => failed.push(id);
  player.enqueue(line('a')); player.enqueue(line('b')); player.enqueue(line('c'));
  await flush();
  audio.breaks(); await flush();                     // a: the file is gone while it loads
  audio.finish(); await flush();                     // b plays to its end
  assert.deepEqual(failed, ['a']);
  assert.deepEqual(ids(audio), ['a', 'b', 'c']);
});

test('TC-VPB-003: a line whose play() fails is skipped, reported once, and the conversation goes on', async () => {
  const failed = [];
  const { audio, player } = make();
  player.onLineError = (id) => failed.push(id);
  audio.failNext = true;
  player.enqueue(line('a')); player.enqueue(line('b'));
  await flush(); await flush();
  assert.deepEqual(failed, ['a']);
  assert.deepEqual(ids(audio), ['b']);
});

test('blocked autoplay holds the lines, nothing is lost, and allowAutoplay plays them in order', async () => {
  const blocked = [];
  const { audio, player, speaking } = make();
  player.onBlocked = (l) => blocked.push(l.id);
  audio.blockNext = true;
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id)));
  await flush();
  assert.deepEqual(blocked, ['a']);
  assert.deepEqual(audio.started, []);
  assert.equal(player.queued, 3);
  assert.deepEqual(speaking, []);
  audio.blockNext = false;
  player.allowAutoplay(); await flush();
  audio.finish(); await flush(); audio.finish(); await flush();
  assert.deepEqual(ids(audio), ['a', 'b', 'c']);
});

test('while autoplay is blocked no new attempt is made and onBlocked is called once, even when the refusal is immediate', async () => {
  const blocked = [];
  const audio = fakeAudio();
  audio.play = function play() {                           // an element that refuses at once (a test double), not with a rejected promise
    if (this.blockNext) { const e = new Error('blocked'); e.name = 'NotAllowedError'; throw e; }
    this.started.push({ url: this.src, audible: !this.muted });
  };
  const player = new VoicePlayer({ audio });
  player.onBlocked = (l) => blocked.push(l.id);
  audio.blockNext = true;
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id)));
  assert.deepEqual(blocked, ['a']);
  assert.equal(player.queued, 3);
  audio.blockNext = false;
  player.allowAutoplay();
  assert.deepEqual(ids(audio), ['a']);
  audio.finish(); audio.finish();
  assert.deepEqual(ids(audio), ['a', 'b', 'c']);
});

test('a stop forgets a held autoplay: the next line is tried again', async () => {
  const blocked = [];
  const { audio, player } = make();
  player.onBlocked = (l) => blocked.push(l.id);
  audio.blockNext = true;
  player.enqueue(line('a'));
  await flush();
  player.stop();
  audio.blockNext = false;
  player.enqueue(line('b'));
  await flush();
  assert.deepEqual(blocked, ['a']);
  assert.deepEqual(ids(audio), ['b']);
});

test('claim is asked at most every 3 s', () => {
  const sent = [];
  let now = 10000;
  const { player } = make({ emitClaim: (data) => sent.push(data), clock: () => now });
  player.claim(); player.claim();
  now += CLAIM_EVERY_MS - 1; player.claim();
  assert.equal(sent.length, 1);
  now += 1; player.claim();
  assert.equal(sent.length, 2);
  player.claim({ initial: true, force: true });
  assert.deepEqual(sent.at(-1), { initial: true });
});

test('TC-VPB-003: on a spec-like element a missing line is reported once and the next lines are heard (F1)', async () => {
  const failed = [];
  const audio = specAudio(['/audio/a.wav']);
  const player = new VoicePlayer({ audio });
  player.onLineError = (id) => failed.push(id);
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id)));
  await flush(); await flush(); await flush();
  assert.deepEqual(failed, ['a']);
  assert.deepEqual(ids(audio), ['b']);
  assert.equal(player.playing, true);
  audio.finish(); await flush(); await flush();
  assert.deepEqual(ids(audio), ['b', 'c']);
  assert.deepEqual(failed, ['a']);
  assert.equal(audio.overlaps, 0);
});

test('TC-VPB-002: a stop while a line starts reports no error, and the next line keeps its serial (F1)', async () => {
  const failed = [];
  const ended = [];
  const speaking = [];
  const audio = specAudio();
  const player = new VoicePlayer({ audio, onEnded: (l) => ended.push(l?.serial) });
  player.onLineError = (id) => failed.push(id);
  player.onSpeaking((value) => speaking.push(value));
  player.enqueue(line('a'));
  player.stop();
  player.enqueue(line('b', { serial: 8 }));
  await flush(); await flush();
  assert.deepEqual(failed, []);
  assert.deepEqual(ids(audio), ['b']);
  assert.equal(player.playing, true);
  audio.finish(); await flush();
  assert.deepEqual(ended, [8]);
  assert.deepEqual(speaking, [true, false]);
});

// --- the page wiring: initSound with a fake socket, storage, elements and window (F4) ----------------------------------------

function element(extra = {}) {
  const listeners = {};
  const attributes = {};
  return {
    hidden: true, value: '', textContent: '', ...extra, attributes,
    setAttribute(name, value) { attributes[name] = value; },
    addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
    click() { (listeners.click || []).forEach((f) => f()); },
  };
}

/** the page of initSound on fakes; `stored` is what the device remembered */
function page({ stored = {}, missing = [] } = {}) {
  const handlers = {};
  const socket = { id: 'me', sent: [], on(name, fn) { handlers[name] = fn; }, emit(name, data) { this.sent.push([name, data]); } };
  const values = { ...stored };
  const storage = { get: (key, fallback) => (key in values ? values[key] : fallback), set: (key, value) => { values[key] = String(value); } };
  const speaking = [];
  const warnings = [];
  const win = {
    setInterval: () => 1, clearInterval: () => {}, addEventListener: () => {},
    console: { warn: (...args) => warnings.push(args.join(' ')) },
  };
  globalThis.document = { visibilityState: 'visible', addEventListener: () => {} };
  const audio = specAudio(missing);
  const els = { muteToggle: element(), muteLabel: element(), muteIcon: element(), volume: element(), hint: element() };
  const sound = initSound({ audio, socket, character: { speaking: (v) => speaking.push(v) }, storage, ...els, t: (key) => key, win });
  const server = (name, data) => handlers[name](data);
  return { audio, socket, values, speaking, warnings, els, sound, server };
}

const reload = (id, serial = 1) => ({ url: `/audio/${id}.wav`, serial });

test('TC-VPB-002: the page can stop the voice: the playing line ends, the queue is empty, the character stops talking (F5)', async () => {
  const p = page();
  p.server('audio_reload', reload('a')); p.server('audio_reload', reload('b'));
  await flush(); await flush();
  assert.equal(p.sound.playing, true);
  p.sound.stop();
  await flush();
  assert.equal(p.audio.playing, false);
  assert.equal(p.sound.queued, 0);
  assert.equal(p.speaking.at(-1), false);
  assert.deepEqual(ids(p.audio), ['a']);
});

test('TC-VPB-002: the composer\'s Stop button also stops the voice (F5)', () => {
  const app = readFileSync(new URL('../../templates/static/chat/app.js', import.meta.url), 'utf8');
  const composer = app.slice(app.indexOf('composer = initComposer('));
  assert.match(composer.slice(0, composer.indexOf('});')), /onStop: \(\) => \{ socket\.emit\('chat_stop'\); sound\.stop\(\); \}/);
});

test('TC-VPB-002: a page that is told another page plays stays silent, and plays again when it gets the voice back (F4)', async () => {
  const p = page();
  p.server('audio_owner', { sid: 'other' });
  p.server('audio_reload', reload('a'));
  await flush(); await flush();
  assert.deepEqual(p.audio.started, []);
  p.server('audio_owner', { sid: 'me' });
  p.server('audio_reload', reload('b'));
  await flush(); await flush();
  assert.deepEqual(ids(p.audio), ['b']);
});

test('TC-VPB-002: a muted player drops the waiting lines and the new ones, as IF-112 says; the playing line ends without sound (F6)', async () => {
  const { audio, player, speaking } = make();
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id)));
  await flush();
  player.mute(true);
  assert.equal(player.queued, 0);
  player.enqueue(line('d'));
  assert.equal(player.queued, 0);
  audio.finish(); await flush();
  assert.deepEqual(ids(audio), ['a']);
  assert.deepEqual(speaking, [true, false]);
  player.mute(false);
  player.enqueue(line('e'));
  await flush();
  assert.deepEqual(ids(audio), ['a', 'e']);
});

test('TC-VPB-002: a device that was muted stays muted after a reload and drops the lines; the toggle brings the voice back (F6, F4)', async () => {
  const p = page({ stored: { 'mia.muted': '1' } });
  assert.equal(p.audio.muted, true);
  p.server('audio_reload', reload('a'));
  await flush(); await flush();
  assert.deepEqual(p.audio.started, []);
  assert.deepEqual(p.speaking, []);
  p.els.muteToggle.click();
  assert.equal(p.values['mia.muted'], '0');
  assert.equal(p.els.muteToggle.attributes['aria-checked'], 'false');
  p.server('audio_reload', reload('b'));
  await flush(); await flush();
  assert.deepEqual(p.audio.started, [{ url: '/audio/b.wav', audible: true }]);
});

test('TC-VPB-003: on the page a missing line is reported once in the browser console, no error is shown, and the next line plays (F2)', async () => {
  const p = page({ missing: ['/audio/a.wav'] });
  p.server('audio_reload', reload('a', 1)); p.server('audio_reload', reload('b', 2));
  await flush(); await flush(); await flush();
  assert.equal(p.warnings.length, 1);
  assert.match(p.warnings[0], /\/audio\/a\.wav/);
  assert.equal(p.els.hint.hidden, true);
  assert.deepEqual(ids(p.audio), ['b']);
});
