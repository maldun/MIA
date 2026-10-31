// The page wiring of N-1.1 outside the conversation, on a fake DOM and a fake socket (F6 of the verification report): the status card of a task
// (task-card.js), the status line and the variant label (mood.js), the socket after a logout (account.js).
// Markers: `// mark.req(...)` above a test (trace_check reads Python markers only).  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, fakeSocket, flush } from './fake-dom.mjs';
import { initTaskCards } from '../../templates/static/chat/task-card.js';
import { followStatus, followVariant } from '../../templates/static/chat/mood.js';
import { initAccount } from '../../templates/static/chat/account.js';

const t = (key, vars = {}) => `${key}${Object.keys(vars).length ? JSON.stringify(vars) : ''}`;

// --- the status card of a task (REQ-CLV-023, IF-101 v8 task_status) ------------------------------------------------
function cards() {
  const doc = installDocument();
  const list = doc.createElement('div');
  const socket = fakeSocket();
  const calls = [];
  const api = { pause: async () => { calls.push('pause'); }, resume: async () => { calls.push('resume'); } };
  const stops = [];
  initTaskCards({ list, socket, api, t, onStop: () => stops.push('stop') });
  const button = (label) => list.querySelectorAll('button').find((b) => b.textContent === label);
  return { list, socket, calls, stops, button };
}

const status = (extra = {}) => ({ id: 'm9', task: 'review', phase: 'searching', mode: 'run', paused: false, done: false,
  budget: { seconds: { used: 5, limit: 600 } }, counts: { on_list: 3 }, ...extra });

// mark.req("REQ-CLV-023")
test('TC-CLV-023: two statuses of one task update one card in place (F6)', () => {
  // Given: the card of a running task
  const p = cards();
  p.socket.fire('task_status', status());
  const card = p.list.querySelector('.task-card');
  // When: the next status of the same task arrives
  p.socket.fire('task_status', status({ phase: 'reading', counts: { on_list: 7 } }));
  // Then: still one card, the same element, with the new figures
  assert.equal(p.list.querySelectorAll('.task-card').length, 1);
  assert.equal(p.list.querySelector('.task-card'), card);
  assert.equal(card.querySelector('.task-card-phase').textContent, 'reading');
  assert.equal(card.querySelector('.task-card-counts dd').textContent, '7');
});

// mark.req("REQ-CLV-023")
test('TC-CLV-023: Pause pauses, a paused card offers Resume, which resumes; Stop stops (F6)', async () => {
  // Given: the card of a running task
  const p = cards();
  p.socket.fire('task_status', status());
  // When: Pause is clicked
  p.button('task.pause').click();
  await flush();
  // Then: the pause call is sent
  assert.deepEqual(p.calls, ['pause']);
  // When: the task says it is paused and Resume is clicked, then Stop
  p.socket.fire('task_status', status({ paused: true }));
  p.button('task.resume').click();
  await flush();
  p.button('task.stop').click();
  // Then: resume is sent and the stop goes out once
  assert.deepEqual(p.calls, ['pause', 'resume']);
  assert.deepEqual(p.stops, ['stop']);
});

// mark.req("REQ-CLV-023")
test('TC-CLV-023: a finished card stays with the final figures and without buttons (F6)', () => {
  // Given: a running card
  const p = cards();
  p.socket.fire('task_status', status());
  // When: the task is done
  p.socket.fire('task_status', status({ done: true, counts: { on_list: 12 } }));
  // Then: the card stays, shows the final count and has no buttons
  assert.equal(p.list.querySelectorAll('.task-card').length, 1);
  assert.equal(p.list.querySelector('.task-card-counts dd').textContent, '12');
  assert.equal(p.list.querySelectorAll('button').length, 0);
});

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
