// The page side of IF-111 (N-1.2 T-01, T-04): TC-CHV-001, TC-CHV-002, TC-CHV-012. node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { initCharacter, LOAD_TIMEOUT_MS } from '../../templates/static/chat/character.js';

const ORIGIN = 'https://mia.local';

function setup(options = {}) {
  const sent = [];
  const frame = { hidden: false, src: '/character/index.html', contentWindow: { postMessage: (text, origin) => sent.push({ message: JSON.parse(text), origin }) },
                  removeAttribute(name) { if (name === 'src') this.src = null; } };
  const handlers = {};
  const socket = { on: (name, fn) => { handlers[name] = fn; }, emit: (name) => sent.push({ emitted: name }) };
  let listener;
  const timers = [];
  const win = { addEventListener: (name, fn) => { if (name === 'message') listener = fn; }, isSecureContext: true,
                setTimeout: (fn, ms) => { timers.push({ fn, ms }); return timers.length; }, clearTimeout: () => {} };
  const events = { failed: [], ready: 0, unmapped: [] };
  const api = initCharacter({ frame, socket, origin: ORIGIN, win, hasWebgl: () => true,
                              onReady: () => { events.ready += 1; }, onFailed: (reason) => events.failed.push(reason), onUnmapped: (p, g) => events.unmapped.push({ p, g }), ...options });
  const fromCharacter = (data, origin = ORIGIN, source = frame.contentWindow) => listener({ origin, source, data: typeof data === 'string' ? data : JSON.stringify(data) });
  return { api, frame, sent, handlers, events, timers, fromCharacter };
}

test('TC-CHV-002: the expression of the server goes to the character as one message with the name', () => {
  const { handlers, sent } = setup();
  handlers.expression({ name: 'happy' });
  assert.deepEqual(sent, [{ message: { type: 'expression', name: 'happy' }, origin: ORIGIN }]);
});

test('TC-CHV-002: speaking, inset, view and background use the same bridge', () => {
  const { api, sent } = setup();
  api.speaking(true); api.setInset({ left: 0, right: 432, top: 0, bottom: 0, width: 1440, height: 900 }); api.setView('bust'); api.setBackground('room.jpg');
  assert.deepEqual(sent.map((s) => s.message.type), ['speaking', 'viewport_inset', 'view', 'background']);
  assert.deepEqual(sent[0].message, { type: 'speaking', value: true });
});

test('ready: the page is told once, the server is told, and the load timer ends', () => {
  const { events, fromCharacter, sent, api } = setup();
  fromCharacter({ type: 'ready' });
  assert.equal(events.ready, 1);
  assert.equal(api.ready, true);
  assert.deepEqual(sent.filter((s) => s.emitted), [{ emitted: 'character_ready' }]);
});

test('TC-CHV-001: a character that says failed hides the iframe, is reported once, and later messages change nothing', () => {
  const { api, frame, events, fromCharacter, sent } = setup();
  fromCharacter({ type: 'failed', reason: 'no WebGL' });
  fromCharacter({ type: 'failed', reason: 'again' });
  assert.deepEqual(events.failed, ['no WebGL']);
  assert.equal(frame.hidden, true);
  assert.equal(frame.src, null);
  assert.equal(api.enabled, false);
  api.speaking(true);
  assert.deepEqual(sent, []);                                  // nothing is sent to a character that is gone
});

test('TC-CHV-001: no answer within the load timeout counts as failed', () => {
  const { events, timers, frame } = setup();
  assert.equal(timers[0].ms, LOAD_TIMEOUT_MS);
  timers[0].fn();
  assert.equal(events.failed.length, 1);
  assert.equal(frame.hidden, true);
});

test('TC-CHV-001: a browser without WebGL never loads the iframe and says why', () => {
  const { events, frame } = setup({ hasWebgl: () => false });
  assert.equal(frame.hidden, true);
  assert.equal(events.failed.length, 1);
});

test('TC-CHV-012: over plain HTTP from a LAN address (not a secure context) the character does not load', () => {
  const win = { addEventListener() {}, isSecureContext: false, setTimeout: () => 1, clearTimeout() {} };
  const { events, frame } = setup({ win, secure: false });
  assert.equal(frame.hidden, true);
  assert.equal(frame.src, null);
  assert.deepEqual(events.failed, ['insecure']);
});

test('TC-CHV-012: on localhost or over HTTPS (a secure context) it loads', () => {
  const { events, frame, timers } = setup({ secure: true });
  assert.equal(frame.hidden, false);
  assert.deepEqual(events.failed, []);
  assert.equal(timers.length, 1);
});

test('a message from another origin, from another window, or that is not JSON is ignored', () => {
  const { events, fromCharacter, sent } = setup();
  fromCharacter({ type: 'ready' }, 'https://evil.example');
  fromCharacter({ type: 'ready' }, ORIGIN, { other: true });
  fromCharacter('{not json');
  fromCharacter({ type: 'something-new' });
  assert.equal(events.ready, 0);
  assert.deepEqual(sent, []);
});

test('unmapped: what a new model cannot map is passed on to the page', () => {
  const { events, fromCharacter } = setup();
  fromCharacter({ type: 'unmapped', presets: ['wink'], gestures: ['bow'] });
  assert.deepEqual(events.unmapped, [{ p: ['wink'], g: ['bow'] }]);
});
