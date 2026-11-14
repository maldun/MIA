// The page wiring of N-1.1 outside the conversation, on a fake DOM and a fake socket (F6 of the verification report): the status line and the variant label (mood.js), the socket after a logout (account.js).
// Markers: `// mark.req(...)` above a test (trace_check reads Python markers only).  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, fakeSocket, flush } from './fake-dom.mjs';
import { followStatus, followVariant } from '../../templates/static/chat/mood.js';
import { initAccount } from '../../templates/static/chat/account.js';

const t = (key, vars = {}) => `${key}${Object.keys(vars).length ? JSON.stringify(vars) : ''}`;

// --- the status line and the variant label (REQ-CLV-008, REQ-CLV-013) -----------------------------------------------
// mark.req("REQ-CLV-008")
test('TC-CLV-008: chat_status updates the mood line, the busy state of the composer and the model chip (F6)', () => {
  // Given: the status line on a fake socket
  const doc = installDocument();
  const socket = fakeSocket();
  const moods = [];
  const busy = [];
  const chip = doc.createElement('span');
  followStatus({ socket, mood: { update: (mood, activity) => moods.push([mood.text, activity]) }, chip, composer: () => ({ setBusy: (v) => busy.push(v) }), t });
  // When: the server says MIA thinks with the light model
  socket.fire('chat_status', { busy: true, activity: 'thinking', profile: 'light', model: 'gemma', mood: { emoji: '🙂', text: 'curious' } });
  // Then: the mood line, the composer and the chip follow
  assert.deepEqual(moods, [['curious', 'thinking']]);
  assert.deepEqual(busy, [true]);
  assert.equal(chip.textContent, 'chip.light');
  assert.equal(chip.hidden, false);
});

// mark.req("REQ-CLV-013")
test('TC-CLV-013: a variant shows its label and goes to the character; a run without one hides the label (F6)', () => {
  // Given: the label and a character that records its variant
  const doc = installDocument();
  const socket = fakeSocket();
  const label = doc.createElement('span');
  const variants = [];
  followVariant({ socket, label, character: { setVariant: (name) => variants.push(name) }, t });
  // When: a run with the variant summer starts, then one without
  socket.fire('variant', { name: 'summer' });
  const shown = [label.textContent, label.hidden];
  socket.fire('variant', { name: null });
  // Then: the label came and went, the character got both
  assert.deepEqual(shown, ['variant.label{"name":"summer"}', false]);
  assert.equal(label.hidden, true);
  assert.deepEqual(variants, ['summer', null]);
});

// --- the change of password (REQ-CLV-018, F7) -------------------------------------------------------------------------
function accountDialog(location) {
  const doc = installDocument();
  const make = (tag) => doc.createElement(tag);
  const parts = { dialog: make('dialog'), nameEl: make('span'), form: make('form'), oldInput: make('input'), newInput: make('input'), repeatInput: make('input'),
    errorLine: make('p'), closeButton: make('button'), logoutButton: make('button') };
  const sent = [];
  const api = { changePassword: async (...args) => { sent.push(args); return { changed: true }; }, whoami: async () => ({ user: 'anna' }) };
  initAccount({ ...parts, api, storage: { get: () => '', set() {} }, t, location });
  parts.oldInput.value = 'pw-anna';
  parts.newInput.value = 'long-enough-1';
  parts.repeatInput.value = 'long-enough-1';
  return { parts, sent };
}

// mark.req("REQ-CLV-018")
test('TC-CLV-018: over plain HTTP from a LAN address the change of password sends nothing and says why (F7)', async () => {
  // Given: the account dialog of a page opened as http://192.168.1.20, filled correctly
  const { parts, sent } = accountDialog({ protocol: 'http:', hostname: '192.168.1.20' });
  // When: the form is sent
  parts.form.requestSubmit();
  await flush();
  // Then: no request, and the reason is shown
  assert.deepEqual(sent, []);
  assert.equal(parts.errorLine.textContent, 'login.insecure');
  assert.equal(parts.errorLine.hidden, false);
});

// mark.req("REQ-CLV-018", "REQ-CLV-014")
test('TC-CLV-018: over HTTPS the same form sends the change once (F7)', async () => {
  // Given: the same dialog on https
  const { parts, sent } = accountDialog({ protocol: 'https:', hostname: 'mia.example' });
  // When: the form is sent
  parts.form.requestSubmit();
  await flush();
  // Then: one change with the old and the new password
  assert.deepEqual(sent, [['pw-anna', 'long-enough-1']]);
});

// --- the logout closes the socket (REQ-CLV-022) ----------------------------------------------------------------------
// mark.req("REQ-CLV-022")
test('TC-CLV-022: after the logout the page closes its socket before the login is shown (F6)', async () => {
  // Given: the account dialog with a socket and a REST client whose logout works
  const doc = installDocument();
  const make = (tag) => doc.createElement(tag);
  const socket = fakeSocket();
  const order = [];
  socket.disconnect = () => order.push('socket closed');
  const parts = { dialog: make('dialog'), nameEl: make('span'), form: make('form'), oldInput: make('input'), newInput: make('input'), repeatInput: make('input'),
    errorLine: make('p'), closeButton: make('button'), logoutButton: make('button') };
  initAccount({ ...parts, socket, api: { logout: async () => ({ loggedOut: true }) }, storage: { get: () => '', set() {} }, t, onLoggedOut: () => order.push('login shown') });
  // When: the user logs out
  parts.logoutButton.click();
  await flush();
  // Then: the socket is closed, then the login is shown
  assert.deepEqual(order, ['socket closed', 'login shown']);
});
