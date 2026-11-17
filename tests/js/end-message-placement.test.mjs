// The end message of a skill run is a new message at the end of the chat (REQ-WFM-036, TC-WFM-036), also when its id is older than the questions of the run:
// the run keeps the id of its first message, so a sort by id put the end bubble below the command and above the questions (finding of the first real /review, 2026-11-17).
// node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, fakeSocket, fakeWindow } from './fake-dom.mjs';
import { initChat } from '../../templates/static/chat/chat.js';

const t = (key) => key;

function page() {
  const doc = installDocument();
  const make = (tag) => doc.createElement(tag);
  const els = { list: make('div'), empty: make('p'), jump: make('button'), olderButton: make('button') };
  const socket = fakeSocket();
  globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => ({ messages: [], older: false }) });
  initChat({ ...els, socket, render: (text) => text, t, origin: 'http://127.0.0.1:8686', win: fakeWindow(), notify: () => {}, me: () => 'anna', api: null });
  const ids = () => [...els.list.children].filter((k) => k.dataset?.id).map((k) => k.dataset.id);
  return { ...els, socket, ids };
}

const created = (second) => new Date(Date.UTC(2026, 10, 17, 22, 0, second)).toISOString();
const message = (id, role, text, second, extra = {}) => ({ id, role, text, created: created(second), ...extra });

test('TC-WFM-036: the end message of a run with questions is the last element, below the questions and the answers', () => {
  // Given: the command, then (ids later than the run's own) a question, the answer and a second question of the run r1
  const p = page();
  p.socket.fire('chat_message', message('0100', 'user', '/review devops', 1));
  p.socket.fire('chat_message', message('0300', 'assistant', 'Which period?', 3, { skill_run: '0200', kind: 'question' }));
  p.socket.fire('chat_message', message('0400', 'user', 'yes', 4));
  p.socket.fire('chat_message', message('0500', 'assistant', 'Cap reached. continue?', 5, { skill_run: '0200', kind: 'question' }));
  p.socket.fire('chat_message', message('0600', 'user', 'summarize', 6));
  // When: the run ends: its end message has the id of the run (0200, older than the questions) and arrives as chat_start, chat_delta, chat_done
  p.socket.fire('chat_start', { id: '0200', role: 'assistant', created: created(2), skill_run: '0200' });
  p.socket.fire('chat_delta', { id: '0200', text: 'The works agree.' });
  p.socket.fire('chat_done', { id: '0200', text: 'The works agree. [Open in the Skill run view](#run=0200)', status: 'done', skill_run: '0200' });
  // Then: it is the last element, after the last answer
  assert.deepEqual(p.ids(), ['0100', '0300', '0400', '0500', '0600', '0200']);
});

test('TC-WFM-036: an ordinary answer is still the last element', () => {
  // Given: a question of a user
  const p = page();
  p.socket.fire('chat_message', message('0100', 'user', 'hi', 1));
  // When: the answer streams in
  p.socket.fire('chat_start', { id: '0200', role: 'assistant', created: created(2) });
  p.socket.fire('chat_delta', { id: '0200', text: 'Hello.' });
  p.socket.fire('chat_done', { id: '0200', text: 'Hello.', status: 'done' });
  // Then: it is below the question
  assert.deepEqual(p.ids(), ['0100', '0200']);
});
