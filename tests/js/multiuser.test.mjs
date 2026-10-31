// The slice of N-1.1 that IF-101 v0 allows: sender of a message, queue position, login, secure channel, endpoints of the page.
// TC-CLV-001, TC-CLV-002, TC-CLV-014, TC-CLV-015, TC-CLV-018, TC-CLV-021.  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { continuesGroup, senderName, queueText } from '../../templates/static/chat/chat-model.js';
import { secureChannel, submitLogin, loginErrorKey } from '../../templates/static/chat/login.js';

const t = (key, vars = {}) => `${key}${Object.keys(vars).length ? JSON.stringify(vars) : ''}`;
const at = (minutes) => new Date(Date.UTC(2026, 0, 1, 12, minutes)).toISOString();

// --- TC-CLV-001: two users' messages show their names ---------------------------------------------------
test('TC-CLV-001: a message of another account shows that name, mine shows "You", MIA shows her name', () => {
  assert.equal(senderName({ role: 'user', sender: 'ben' }, 'anna', t), 'ben');
  assert.equal(senderName({ role: 'user', sender: 'anna' }, 'anna', t), 'chat.you');
  assert.equal(senderName({ role: 'assistant', sender: 'MIA' }, 'anna', t), 'app.title');
  assert.equal(senderName({ role: 'user' }, 'anna', t), 'chat.you');                    // the old server sends no sender: as before
  assert.equal(senderName({ role: 'user', sender: 'ben' }, null, t), 'ben');            // my account is not known (a kept session): names are shown
});

test('TC-CLV-001: messages of two users do not make one group, messages of one user close in time do', () => {
  const anna = { role: 'user', sender: 'anna', created: at(0) };
  assert.equal(continuesGroup(anna, { role: 'user', sender: 'ben', created: at(1) }), false);
  assert.equal(continuesGroup(anna, { role: 'user', sender: 'anna', created: at(1) }), true);
  assert.equal(continuesGroup({ role: 'user', created: at(0) }, { role: 'user', created: at(1) }), true);        // old messages without sender
});

// --- TC-CLV-002: the queue shows positions ------------------------------------------------------------------
test('TC-CLV-002: a waiting message shows its position, positions 1, 2 and 3 are all shown', () => {
  assert.deepEqual([1, 2, 3].map((n) => queueText({ local: 'queued', position: n }, t)), ['chat.position{"n":1}', 'chat.position{"n":2}', 'chat.position{"n":3}']);
});

test('TC-CLV-002: without a position (the old server) the text stays "Waiting"; a message that is not waiting shows nothing', () => {
  assert.equal(queueText({ local: 'queued' }, t), 'chat.waiting');
  assert.equal(queueText({ local: undefined, position: 2 }, t), '');
});

// --- TC-CLV-018: a password goes only over HTTPS or to localhost ---------------------------------------------
test('TC-CLV-018: secure channel = HTTPS, or localhost, 127.0.0.1 and ::1 over HTTP', () => {
  assert.equal(secureChannel({ protocol: 'https:', hostname: 'mia.example' }), true);
  assert.equal(secureChannel({ protocol: 'http:', hostname: 'localhost' }), true);
  assert.equal(secureChannel({ protocol: 'http:', hostname: '127.0.0.1' }), true);
  assert.equal(secureChannel({ protocol: 'http:', hostname: '[::1]' }), true);
  assert.equal(secureChannel({ protocol: 'http:', hostname: '192.168.1.20' }), false);
  assert.equal(secureChannel({ protocol: 'http:', hostname: 'mia.local' }), false);
});

test('TC-CLV-018: over plain HTTP from a LAN address the login form sends nothing', async () => {
  let calls = 0;
  const result = await submitLogin({ user: 'anna', password: 'pw', location: { protocol: 'http:', hostname: '192.168.1.20', origin: 'http://192.168.1.20:8585' }, fetchFn: async () => { calls += 1; } });
  assert.deepEqual(result, { ok: false, error: 'insecure' });
  assert.equal(calls, 0);
});

// --- TC-CLV-014: the login ----------------------------------------------------------------------------------
const secure = { protocol: 'https:', hostname: 'mia.example', origin: 'https://mia.example' };

test('TC-CLV-014: the login sends account and password once to /api/login as JSON and reports success', async () => {
  const sent = [];
  const fetchFn = async (url, init) => { sent.push({ url: String(url), init }); return { ok: true, status: 200, json: async () => ({}) }; };
  const result = await submitLogin({ user: 'anna', password: 'pw-anna', location: secure, fetchFn });
  assert.deepEqual(result, { ok: true, user: 'anna' });
  assert.equal(sent.length, 1);
  assert.equal(sent[0].url, 'https://mia.example/api/login');
  assert.equal(sent[0].init.method, 'POST');
  assert.equal(sent[0].init.credentials, 'same-origin');
  assert.deepEqual(JSON.parse(sent[0].init.body), { user: 'anna', password: 'pw-anna' });
});

test('TC-CLV-014: wrong credentials, throttling and a lost connection give three different messages', async () => {
  const answer = (status) => async () => { if (status === 0) throw new Error('offline'); return { ok: false, status, json: async () => ({}) }; };
  const results = [];
  for (const status of [401, 429, 0, 500]) results.push(await submitLogin({ user: 'anna', password: 'x', location: secure, fetchFn: answer(status) }));
  assert.deepEqual(results.map((r) => r.ok), [false, false, false, false]);
  assert.deepEqual(results.map((r) => loginErrorKey(r.error)), ['login.bad', 'login.throttled', 'login.failed', 'login.failed']);
});

test('TC-CLV-014: a refusal of the server because of the channel or the address is named, not shown as "is MIA reachable?"', async () => {
  const refused = (error) => async () => ({ ok: false, status: 403, json: async () => ({ error }) });
  const insecure = await submitLogin({ user: 'anna', password: 'x', location: secure, fetchFn: refused('insecure_channel') });
  const origin = await submitLogin({ user: 'anna', password: 'x', location: secure, fetchFn: refused('bad_origin') });
  const other = await submitLogin({ user: 'anna', password: 'x', location: secure, fetchFn: refused('something_else') });
  assert.deepEqual([insecure.error, origin.error, other.error], ['insecure', 'origin', 'failed']);
  assert.deepEqual([insecure, origin, other].map((r) => loginErrorKey(r.error)), ['login.insecure', 'login.origin', 'login.failed']);
});

test('TC-CLV-014: an empty account or password is not sent', async () => {
  let calls = 0;
  const fetchFn = async () => { calls += 1; };
  assert.deepEqual(await submitLogin({ user: '', password: 'x', location: secure, fetchFn }), { ok: false, error: 'empty' });
  assert.deepEqual(await submitLogin({ user: 'anna', password: '', location: secure, fetchFn }), { ok: false, error: 'empty' });
  assert.equal(calls, 0);
});

// --- TC-CLV-015: the login page tells that all is visible ------------------------------------------------------
test('TC-CLV-015: the login page states that everything is visible to all users, in both languages', () => {
  const dir = new URL('../../templates/static/chat/i18n/', import.meta.url).pathname;
  const en = JSON.parse(readFileSync(join(dir, 'en.json'), 'utf8'));
  const de = JSON.parse(readFileSync(join(dir, 'de.json'), 'utf8'));
  assert.match(en['login.visible'], /everything .* visible to all users/i);
  assert.match(de['login.visible'], /alle/i);
  const html = readFileSync(new URL('../../templates/index.html', import.meta.url).pathname, 'utf8');
  assert.ok(html.includes('data-i18n="login.visible"'));
});

test('TC-CLV-015: the login screen has an opaque black backdrop, so the app behind it is not visible before the login', () => {
  const css = readFileSync(new URL('../../templates/static/chat/components.css', import.meta.url).pathname, 'utf8');
  assert.match(css, /#login::backdrop\s*\{\s*background:\s*#000;?\s*\}/);
});

// --- TC-CLV-021: the page uses the calls of IF-101 only ------------------------------------------------------
// The allow-list is read from the contract (D-163 F4), by the rules of contractWire in tests/test_chat_views_browser.py: an operation `name(...)` is at
// /api/<name>; a name in brackets after it, (`chat_send`), and a name after the word event are socket events; an address in backquotes is a path;
// the first column of every events table is an event.
// Used by the page and the backend but not yet in IF-101 v13: amendment A-62 adds them to IF-101 v14 and empties this set.
const PENDING_A62 = new Set(['/api/chat/commands', '/character-backgrounds.json',
  'chat_pipeline', 'audio_claim', 'audio_owner', 'audio_reload', 'audio_ended', 'character_ready']);
const SOCKET_IO_OWN = new Set(['connect', 'disconnect', 'connect_error']);          // events of the Socket.IO client itself, never on the wire

function contractWire(text) {
  const paths = new Set();
  const events = new Set();
  let inEvents = false;
  for (const line of text.split('\n')) {
    inEvents ||= line.startsWith('Events (');
    if (!line.startsWith('| `')) continue;
    const cell = line.split('|')[1];
    if (inEvents) {
      const first = cell.match(/`([a-z_]+)`/);
      if (first) events.add(first[1]);
      continue;
    }
    for (const m of cell.matchAll(/`([a-z_]+)\(/g)) paths.add(`/api/${m[1]}`);
    for (const m of cell.matchAll(/\(`([a-z_]+)`\)/g)) events.add(m[1]);
    for (const m of line.matchAll(/event `([a-z_]+)`/g)) events.add(m[1]);
    for (const m of cell.matchAll(/`(\/[a-z_/.<>-]+)`/g)) paths.add(m[1].split('<')[0]);
  }
  return { paths, events };
}

test('TC-CLV-021: the wire is read from the contract text by the same rules as the browser test', () => {
  // Given: rows of the operations table and of the events table
  const text = ['| `send(session, text)` (`chat_send`) | text | ack |', '| `file(session, name)` (`/api/files/<name>`) | name | bytes |',
    '| `connect(session)` | session | event `chat_status` first | |', 'Events (server to every connected page):', '| `chat_start` | `{id}` |'].join('\n');
  // When: the wire is read
  const { paths, events } = contractWire(text);
  // Then: the paths and events of the rows, nothing else
  assert.deepEqual([...paths].sort(), ['/api/connect', '/api/file', '/api/files/', '/api/send']);
  assert.deepEqual([...events].sort(), ['chat_send', 'chat_start', 'chat_status']);
});

test('TC-CLV-021: every address and socket event the page uses is named in IF-101 (D-163 F4)', () => {
  const dir = new URL('../../templates/static/chat/', import.meta.url).pathname;
  const wire = contractWire(readFileSync(new URL('../../contracts/IF-101-chat-api.md', import.meta.url).pathname, 'utf8'));
  const allowedPaths = new Set([...wire.paths, ...PENDING_A62]);
  const allowedEvents = new Set([...wire.events, ...PENDING_A62, ...SOCKET_IO_OWN]);
  const paths = new Set();
  const events = new Set();
  for (const file of readdirSync(dir).filter((f) => f.endsWith('.js'))) {
    const text = readFileSync(join(dir, file), 'utf8');
    for (const m of text.matchAll(/['"`](\/(?:api|character-backgrounds)[A-Za-z0-9_./-]*)['"`]/g)) paths.add(m[1]);
    for (const m of text.matchAll(/socket(?:\.timeout\(\d+\))?\.(?:on|emit)\('([a-z_]+)'/g)) events.add(m[1]);
  }
  assert.deepEqual([...paths].filter((p) => !allowedPaths.has(p)), []);
  assert.deepEqual([...events].filter((e) => !allowedEvents.has(e)), []);
  assert.ok(paths.has('/api/login'), 'the login call is used');
});
