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
