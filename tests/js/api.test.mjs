// The REST client of the page (IF-101 v1): one function per operation, errors with status and code, a lost session asks for the login.
// REQ-CLV-021 (the page uses the interface only), REQ-CLV-005, -009 to -012, -014.  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, createApi } from '../../templates/static/chat/api.js';

function setup(answer = () => ({ status: 200, body: {} })) {
  const calls = [];
  let login = 0;
  const fetchFn = async (url, init = {}) => {
    const u = new URL(url);
    calls.push({ method: init.method ?? 'GET', path: u.pathname, query: Object.fromEntries(u.searchParams), body: init.body ? JSON.parse(init.body) : undefined, credentials: init.credentials });
    const { status, body } = answer(calls.at(-1));
    return { ok: status >= 200 && status < 300, status, json: async () => body };
  };
  const api = createApi({ origin: 'https://mia.example', fetchFn, onLoginRequired: () => { login += 1; } });
  return { api, calls, logins: () => login };
}

test('every operation has its own address, method and body, and sends the session cookie', async () => {
  const { api, calls } = setup();
  await api.whoami();
  await api.changePassword('old-secret', 'new-secret-1');
  await api.regenerate('m5');
  await api.speakAgain('m5');
  await api.account('m5');
  await api.vote('m5', 'answer_quality', 1);
  await api.score();
  await api.items('tasks');
  await api.saveItem('memory', null, 'likes tea', 'chat');
  await api.deleteItem('memos', 'm7');
  await api.trust();
  await api.setTrust('example.org', 0.2);
  await api.persona();
  await api.savePersona({ text: 'calm' });
  assert.deepEqual(calls.map((c) => `${c.method} ${c.path}`), [
    'GET /api/whoami', 'POST /api/change_password', 'POST /api/regenerate', 'POST /api/speak_again', 'GET /api/account', 'POST /api/vote', 'GET /api/score',
    'GET /api/items', 'POST /api/items', 'DELETE /api/items', 'GET /api/trust', 'POST /api/trust', 'GET /api/persona', 'POST /api/persona',
  ]);
  assert.ok(calls.every((c) => c.credentials === 'same-origin'));
  assert.deepEqual(calls[1].body, { old: 'old-secret', new: 'new-secret-1' });
  assert.deepEqual(calls[5].body, { subject: 'm5', category: 'answer_quality', value: 1 });
  assert.deepEqual(calls[4].query, { message_id: 'm5' });
  assert.deepEqual(calls[8].body, { kind: 'memory', id: null, text: 'likes tea', source: 'chat' });
  assert.deepEqual(calls[9].query, { kind: 'memos', id: 'm7' });
  assert.deepEqual(calls[11].body, { source: 'example.org', value: 0.2 });
  assert.deepEqual(calls[13].body, { doc: { text: 'calm' } });
});

test('the answer of the server is the result', async () => {
  const { api } = setup(() => ({ status: 200, body: { user: 'anna' } }));
  assert.deepEqual(await api.whoami(), { user: 'anna' });
});

test('an error carries the status, the code and the rule of the server', async () => {
  const { api } = setup(() => ({ status: 422, body: { error: 'invalid_item', rule: 'source' } }));
  await assert.rejects(api.saveItem('memory', null, 'x', null), (error) => error instanceof ApiError && error.status === 422 && error.code === 'invalid_item' && error.rule === 'source');
});

test('a lost session asks for the login once per call and the call still fails', async () => {
  const { api, logins } = setup(() => ({ status: 401, body: { error: 'unauthenticated' } }));
  await assert.rejects(api.score(), (error) => error.status === 401);
  assert.equal(logins(), 1);
});

test('a lost connection is an error with status 0', async () => {
  const api = createApi({ origin: 'https://mia.example', fetchFn: async () => { throw new Error('offline'); } });
  await assert.rejects(api.score(), (error) => error instanceof ApiError && error.status === 0 && error.code === 'offline');
});

test('a wrong password is shown as a wrong password and does not ask for the login', async () => {
  const { api, logins } = setup(() => ({ status: 401, body: { error: 'bad_credentials' } }));
  await assert.rejects(api.changePassword('x', 'long-enough-1'), (error) => error.code === 'bad_credentials');
  assert.equal(logins(), 0);
});
