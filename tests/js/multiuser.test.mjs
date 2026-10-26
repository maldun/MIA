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

// --- TC-CLV-021: the page uses the calls of IF-101 only ------------------------------------------------------
test('TC-CLV-021: every address and socket event the page uses is one of the interface (or of the character and the voice)', () => {
  const dir = new URL('../../templates/static/chat/', import.meta.url).pathname;
  const allowedPaths = new Set(['/api/login', '/api/chat/history', '/api/chat/commands', '/character-backgrounds.json',
    '/api/whoami', '/api/change_password', '/api/regenerate', '/api/speak_again', '/api/account', '/api/vote', '/api/score', '/api/items', '/api/trust', '/api/persona']);   // IF-101 v1
  const allowedEvents = new Set(['chat_send', 'chat_stop', 'character_ready', 'audio_claim', 'audio_ended', 'chat_message', 'chat_start', 'chat_delta', 'chat_done', 'chat_status',
    'chat_pipeline', 'chat_error', 'expression', 'audio_reload', 'audio_owner', 'connect', 'disconnect', 'connect_error',
    'variant', 'score', 'item_changed', 'trust_changed', 'persona_changed']);                                                                                                  // IF-101 v1
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
