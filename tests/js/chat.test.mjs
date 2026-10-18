// Pure parts of the conversation: node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { upsert, trimOldest, continuesGroup, dayKey, dayLabel, relativeTime, linkify, filterCommands, emojiFor, modelLabel } from '../../templates/static/chat/chat-model.js';

const t = (key, vars = {}) => key + (vars.n !== undefined ? `:${vars.n}` : '');
const at = (iso) => new Date(iso).toISOString();

test('upsert keeps the list sorted and replaces by id', () => {
  const list = [];
  upsert(list, { id: '003', text: 'c' });
  upsert(list, { id: '001', text: 'a' });
  upsert(list, { id: '002', text: 'b' });
  assert.deepEqual(list.map((m) => m.id), ['001', '002', '003']);
  const index = upsert(list, { id: '002', text: 'B' });
  assert.equal(index, 1);
  assert.equal(list.length, 3);
  assert.equal(list[1].text, 'B');
});

test('upsert upgrades a local message by its client id', () => {
  const list = [{ id: '~1', client_id: 'x', role: 'user', text: 'hi', local: 'sending' }];
  const index = upsert(list, { id: '0001', client_id: 'x', local: undefined });
  assert.equal(index, 0);
  assert.equal(list.length, 1);
  assert.equal(list[0].id, '0001');
  assert.equal(list[0].text, 'hi');
  assert.equal(list[0].local, undefined);
});

test('the oldest messages leave the window', () => {
  const list = Array.from({ length: 10 }, (_, i) => ({ id: String(i) }));
  const removed = trimOldest(list, 4);
  assert.deepEqual(removed.map((m) => m.id), ['0', '1', '2', '3', '4', '5']);
  assert.equal(list.length, 4);
  assert.deepEqual(trimOldest(list, 10), []);
});

test('grouping: same sender, close in time, no system notes', () => {
  const a = { role: 'assistant', created: '2026-10-18T10:00:00Z' };
  assert.equal(continuesGroup(a, { role: 'assistant', created: '2026-10-18T10:03:00Z' }), true);
  assert.equal(continuesGroup(a, { role: 'assistant', created: '2026-10-18T10:09:00Z' }), false);
  assert.equal(continuesGroup(a, { role: 'user', created: '2026-10-18T10:01:00Z' }), false);
  assert.equal(continuesGroup(a, { role: 'assistant', auto: true, created: '2026-10-18T10:01:00Z' }), false);
  assert.equal(continuesGroup({ role: 'system', created: a.created }, { role: 'system', created: a.created }), false);
  assert.equal(continuesGroup(undefined, a), false);
});

test('day labels', () => {
  const now = new Date(2026, 9, 18, 12, 0, 0);
  assert.equal(dayLabel(new Date(2026, 9, 18, 8, 0).toISOString(), now, t), 'time.today');
  assert.equal(dayLabel(new Date(2026, 9, 17, 23, 0).toISOString(), now, t), 'time.yesterday');
  assert.notEqual(dayLabel(new Date(2026, 9, 1, 8, 0).toISOString(), now, t), 'time.today');
  assert.equal(dayKey(new Date(2026, 0, 5, 3)), '2026-01-05');
});

test('relative times', () => {
  const now = new Date('2026-10-18T10:10:00Z');
  assert.equal(relativeTime(at('2026-10-18T10:09:40Z'), now, t), 'time.now');
  assert.equal(relativeTime(at('2026-10-18T10:05:00Z'), now, t), 'time.minutes:5');
  assert.match(relativeTime(at('2026-10-18T07:00:00Z'), now, t), /\d/);
});

test('links in typed text become link parts, other text stays text', () => {
  assert.deepEqual(linkify('see https://example.org/a?b=1, ok'), [
    { text: 'see ' }, { href: 'https://example.org/a?b=1' }, { text: ', ok' },
  ]);
  assert.deepEqual(linkify('no link <b>here</b>'), [{ text: 'no link <b>here</b>' }]);
  assert.deepEqual(linkify('javascript:alert(1)'), [{ text: 'javascript:alert(1)' }]);
});

test('command palette filter', () => {
  const commands = [{ command: '/light!' }, { command: '/full!' }, { command: '/break!' }, { command: '/goodnight!' }];
  assert.equal(filterCommands(commands, '/').length, 4);
  assert.deepEqual(filterCommands(commands, '/Li').map((c) => c.command), ['/light!']);
  assert.deepEqual(filterCommands(commands, 'hello /'), []);
  assert.deepEqual(filterCommands(commands, '/light! now'), []);
  assert.deepEqual(filterCommands(commands, '/zzz'), []);
});

test('emotion badges and model chip', () => {
  assert.equal(emojiFor('happy'), '😄');
  assert.equal(emojiFor('MIA'), '👋');
  assert.equal(emojiFor('unknown'), '😊');
  assert.equal(emojiFor(null), '');
  assert.equal(modelLabel('light'), 'light');
  assert.equal(modelLabel('x'), '');
});
