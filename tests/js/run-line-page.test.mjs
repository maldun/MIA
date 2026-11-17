// The page wiring of the status line of a skill run (chat.js, A-158, REQ-CLV-053, 054) on a fake DOM and a fake socket. node --test "tests/js/*.test.mjs"
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
  const kids = () => [...els.list.children];
  const lines = () => kids().filter((k) => k.className === 'run-line');
  return { ...els, socket, kids, lines };
}

const message = (id, text, extra = {}) => ({ id, role: 'assistant', text, created: new Date(Date.UTC(2026, 10, 17, 12, 0, Number(id))).toISOString(), ...extra });

test('TC-CLV-053: a line is set, a message arrives, the line changes: one line, still the last element', () => {
  // Given: the page with one message and the line `collect`
  const p = page();
  p.socket.fire('chat_message', message('1', 'Question'));
  p.socket.fire('chat_run_status', { run: 'r1', text: 'collect' });
  // When: another message arrives and the line changes to `rank`
  p.socket.fire('chat_message', message('2', 'Answer'));
  p.socket.fire('chat_run_status', { run: 'r1', text: 'rank' });
  // Then: there is one line, it shows `rank` and it is the last element of the list
  assert.equal(p.lines().length, 1);
  assert.equal(p.kids().at(-1), p.lines()[0]);
  assert.equal(p.lines()[0].querySelector('.run-line-text').textContent, 'rank');
  assert.equal(p.lines()[0].querySelector('a').getAttribute('href') ?? p.lines()[0].querySelector('a').href, '#run=r1');
});

test('TC-CLV-053: when the line is cleared it is gone and the end message is the last element', () => {
  // Given: a line of run r1 and a message
  const p = page();
  p.socket.fire('chat_message', message('1', 'Question'));
  p.socket.fire('chat_run_status', { run: 'r1', text: 'report' });
  // When: the line is cleared and the end message arrives
  p.socket.fire('chat_run_status', { run: 'r1', text: null });
  p.socket.fire('chat_message', message('2', 'Done. [Open in the Skill run view](#run=r1)', { skill_run: 'r1', kind: 'done' }));
  // Then: no line is left and the last element is the row of the end message
  assert.equal(p.lines().length, 0);
  assert.notEqual(p.kids().at(-1).className, 'run-line');
});
