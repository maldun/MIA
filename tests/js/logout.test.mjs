// The logout (REQ-CLV-022, REQ-FE-031; IF-101 v2, amendment A-04): one request, the socket closes, the login is shown.  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { createApi } from '../../templates/static/chat/api.js';
import { initAccount } from '../../templates/static/chat/account.js';

function element() {
  const listeners = {};
  return {
    listeners, value: '', textContent: '', hidden: false, open: false,
    addEventListener(type, fn) { listeners[type] = fn; },
    focus() {}, reset() {}, showModal() { this.open = true; }, close() { this.open = false; },
  };
}

function setup({ logoutFails = false } = {}) {
  const calls = [];
  const fetchFn = async (url, init = {}) => {
    calls.push(`${init.method ?? 'GET'} ${new URL(url).pathname}`);
    const ok = !logoutFails;
    return { ok, status: ok ? 200 : 0, json: async () => (ok ? { loggedOut: true } : {}) };
  };
  const api = createApi({ origin: 'https://mia.example', fetchFn });
  const events = [];
  const parts = { dialog: element(), nameEl: element(), form: element(), oldInput: element(), newInput: element(), repeatInput: element(), errorLine: element(), closeButton: element(), logoutButton: element() };
  const account = initAccount({
    ...parts, api, storage: { get: () => '', set() {} }, t: (key) => key, notify: () => {}, onLoggedOut: () => events.push('logged out'),
  });
  return { calls, parts, events, account };
}

test('TC-CLV-022: the logout sends one request to /api/logout', async () => {
  const sent = [];
  const fetchFn = async (url, init = {}) => { sent.push(`${init.method} ${new URL(url).pathname}`); return { ok: true, status: 200, json: async () => ({ loggedOut: true }) }; };
  const api = createApi({ origin: 'https://mia.example', fetchFn });
  assert.deepEqual(await api.logout(), { loggedOut: true });
  assert.deepEqual(sent, ['POST /api/logout']);
});

test('TC-CLV-022: the logout button closes the account dialog, sends one request and reports the logout', async () => {
  const { calls, parts, events } = setup();
  parts.dialog.open = true;
  await parts.logoutButton.listeners.click();
  assert.deepEqual(calls, ['POST /api/logout']);
  assert.equal(parts.dialog.open, false);
  assert.deepEqual(events, ['logged out']);
});

test('TC-CLV-022: a logout that cannot reach the server says so and does not report a logout', async () => {
  const { parts, events } = setup({ logoutFails: true });
  parts.dialog.open = true;
  await parts.logoutButton.listeners.click();
  assert.deepEqual(events, []);
  assert.equal(parts.errorLine.textContent, 'chat.offline');
  assert.equal(parts.dialog.open, true);
});

test('TC-CLV-022: a session that is already gone (401) counts as logged out', async () => {
  const calls = [];
  const fetchFn = async () => ({ ok: false, status: 401, json: async () => ({ error: 'unauthenticated' }) });
  const api = createApi({ origin: 'https://mia.example', fetchFn, onLoginRequired: () => calls.push('login') });
  const events = [];
  const parts = { dialog: element(), nameEl: element(), form: element(), oldInput: element(), newInput: element(), repeatInput: element(), errorLine: element(), closeButton: element(), logoutButton: element() };
  initAccount({ ...parts, api, storage: { get: () => '', set() {} }, t: (k) => k, onLoggedOut: () => events.push('logged out') });
  await parts.logoutButton.listeners.click();
  assert.deepEqual(events, ['logged out']);
});
