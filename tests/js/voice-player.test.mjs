// The voice player (N-1.3, IF-112): TC-VPB-001 to TC-VPB-003 on a fake audio element. node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { VoicePlayer, CLAIM_EVERY_MS } from '../../templates/static/chat/sound.js';

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
