// The page wiring of the conversation (chat.js, N-1.1) on a fake DOM, a fake socket and a fake fetch: F1 and F6 of the verification report.
// Markers: `// mark.req(...)` above a test, as in the contract suites (trace_check reads Python markers only).  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, fakeSocket, fakeWindow, flush } from './fake-dom.mjs';
import { initChat } from '../../templates/static/chat/chat.js';

const t = (key, vars = {}) => `${key}${Object.keys(vars).length ? JSON.stringify(vars) : ''}`;

/** the conversation on fakes; `history` is what /api/chat/history answers, `api` the REST calls under an answer */
function page({ history = { messages: [], older: false }, api = null, me = 'anna' } = {}) {
  const doc = installDocument();
  const make = (tag) => doc.createElement(tag);
  const els = { list: make('div'), empty: make('p'), jump: make('button'), olderButton: make('button') };
  const socket = fakeSocket();
  const win = fakeWindow();
  const notes = [];
  const requests = [];
  globalThis.fetch = async (url) => { requests.push(String(url)); return { ok: true, status: 200, json: async () => history }; };
  const chat = initChat({ ...els, socket, render: (text) => text, t, origin: 'http://127.0.0.1:8686', win, notify: (n) => notes.push(n), me: () => me, api });
  const row = (id) => chat.rows.get(id);
  const state = (id) => row(id)?.querySelector('[data-role=state]').textContent;
  const bubble = (id) => row(id)?.querySelector('[data-role=bubble]').textContent;
  return { ...els, socket, win, chat, notes, requests, row, state, bubble };
}

const at = (seconds) => new Date(Date.UTC(2026, 9, 31, 12, 0, seconds)).toISOString();

/** the user sends `text`; the server acknowledges it as message `id` at queue `position` (IF-101 send) */
function sendAcked(p, text, id, position) {
  p.chat.send(text);
  const { data, ack } = p.socket.emitted.filter((e) => e.name === 'chat_send').at(-1);
  ack(null, { ok: true, id, position, message: { id, role: 'user', sender: 'anna', text, created: at(Number(id)), client_id: data.id } });
}

// --- F1: the queue positions (REQ-CLV-002) ------------------------------------------------------------------------
// mark.req("REQ-CLV-002")
test('TC-CLV-002: when an answer starts, the message answered loses its place and the others move up one place (F1)', () => {
  // Given: three messages waiting at places 1, 2 and 3
  const p = page();
  sendAcked(p, 'one', '11', 1);
  sendAcked(p, 'two', '12', 2);
  sendAcked(p, 'three', '13', 3);
  assert.deepEqual(['11', '12', '13'].map(p.state), ['chat.position{"n":1}', 'chat.position{"n":2}', 'chat.position{"n":3}']);
  // When: the answer to the first one starts
  p.socket.fire('chat_start', { id: '14', role: 'assistant' });
  // Then: the first shows no place, the second is now first and the third second
  assert.deepEqual(['11', '12', '13'].map(p.state), ['', 'chat.position{"n":1}', 'chat.position{"n":2}']);
  // When: the next answer starts
  p.socket.fire('chat_start', { id: '15', role: 'assistant' });
  // Then: only the last one still waits, now at place 1
  assert.deepEqual(['11', '12', '13'].map(p.state), ['', '', 'chat.position{"n":1}']);
});

// mark.req("REQ-CLV-002")
test('TC-CLV-002: a start of an answer to another user\'s message moves my waiting message up, it does not clear it (F1)', () => {
  // Given: my message waits at place 2 (another user's message is first)
  const p = page();
  sendAcked(p, 'mine', '21', 2);
  // When: the answer to the other message starts
  p.socket.fire('chat_start', { id: '22', role: 'assistant' });
  // Then: mine is answered next
  assert.equal(p.state('21'), 'chat.position{"n":1}');
});

// --- F6: the drawing of the conversation ------------------------------------------------------------------------
// mark.req("REQ-CLV-001")
test('TC-CLV-001: a message of another account shows that name above it, mine shows "You" (F6)', () => {
  // Given: the conversation of anna
  const p = page();
  // When: a message of ben and one of anna arrive
  p.socket.fire('chat_message', { id: '31', role: 'user', sender: 'ben', text: 'hi from ben', created: at(31) });
  p.socket.fire('chat_message', { id: '32', role: 'user', sender: 'anna', text: 'hi from anna', created: at(32) });
  // Then: the rows name ben and "You"
  assert.equal(p.row('31').querySelector('.msg-name').textContent, 'ben');
  assert.equal(p.row('32').querySelector('.msg-name').textContent, 'chat.you');
  assert.equal(p.bubble('31'), 'hi from ben');
});

// mark.req("REQ-CLV-001")
test('TC-CLV-001: an answer streams: each delta is drawn in the same row, the end makes the actions visible (F6)', () => {
  // Given: an answer that started
  const p = page({ api: {} });
  p.socket.fire('chat_start', { id: '41', role: 'assistant' });
  // When: two deltas arrive, each drawn in the next frame
  p.socket.fire('chat_delta', { id: '41', text: 'Hello' });
  p.win.runFrames();
  const first = p.bubble('41');
  p.socket.fire('chat_delta', { id: '41', text: 'Hello anna.' });
  p.win.runFrames();
  // Then: the text grows in one row, and the actions wait for the end
  assert.equal(first, 'Hello');
  assert.equal(p.bubble('41'), 'Hello anna.');
  assert.equal(p.chat.rows.size, 1);
  assert.equal(p.row('41').querySelector('[data-action=up]').hidden, true);
  // When: the answer is done
  p.socket.fire('chat_done', { id: '41', text: 'Hello anna. Fine.', emotion: 'happy', status: 'done' });
  // Then: the final text and the actions are shown
  assert.equal(p.bubble('41'), 'Hello anna. Fine.');
  assert.equal(p.row('41').querySelector('[data-action=up]').hidden, false);
});

// mark.req("REQ-CLV-003")
test('TC-CLV-003: the page loads the last 50 messages in order and adds a live message of another user (F6)', async () => {
  // Given: a history of three messages, sent out of order
  const history = { older: false, messages: [
    { id: '53', role: 'assistant', text: 'third', created: at(53) },
    { id: '51', role: 'user', sender: 'ben', text: 'first', created: at(51) },
    { id: '52', role: 'user', sender: 'anna', text: 'second', created: at(52) },
  ] };
  const p = page({ history });
  // When: the page loads the history and another user writes
  await p.chat.loadLatest();
  p.socket.fire('chat_message', { id: '54', role: 'user', sender: 'carl', text: 'fourth', created: at(54) });
  // Then: one request with limit 50, and the rows in the order of their ids
  assert.equal(p.requests.length, 1);
  assert.equal(new URL(p.requests[0]).pathname, '/api/chat/history');
  assert.equal(new URL(p.requests[0]).searchParams.get('limit'), '50');
  const order = p.list.querySelectorAll('.row').map((r) => r.dataset.id);
  assert.deepEqual(order, ['51', '52', '53', '54']);
});

// mark.req("REQ-CLV-008")
test('TC-CLV-008: "how I got this" draws the steps of the account under the answer, a second click hides them (F6)', async () => {
  // Given: a written answer and a REST client that knows its account
  const asked = [];
  const p = page({ api: { account: async (id) => { asked.push(id); return [{ seq: 1, plain: 'I read your question.' }, { seq: 2, plain: 'I answered.' }]; } } });
  p.socket.fire('chat_start', { id: '61', role: 'assistant' });
  p.socket.fire('chat_done', { id: '61', text: 'Done.', status: 'done' });
  // When: the button is clicked
  p.row('61').querySelector('[data-action=how]').click();
  await flush();
  // Then: the two steps are listed, asked once
  const block = p.row('61').querySelector('.account');
  assert.deepEqual(block.querySelectorAll('li').map((li) => li.textContent), ['I read your question.', 'I answered.']);
  assert.deepEqual(asked, ['61']);
  // When: it is clicked again
  p.row('61').querySelector('[data-action=how]').click();
  await flush();
  // Then: the block is hidden and not asked again
  assert.equal(block.hidden, true);
  assert.equal(asked.length, 1);
});
