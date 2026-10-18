// Page side of the character integration: node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { insetFor } from '../../templates/static/chat/layout.js';
import { captionText } from '../../templates/static/chat/chat-model.js';

test('wide: the panel covers the right side of the window', () => {
  const inset = insetFor({ mode: 'panel', collapsed: false, rect: { left: 1008, top: 12 }, width: 1440, height: 900 });
  assert.deepEqual(inset, { left: 0, right: 432, top: 0, bottom: 0, width: 1440, height: 900 });
});

test('phone: the sheet covers the bottom of the window', () => {
  const inset = insetFor({ mode: 'sheet', collapsed: false, rect: { left: 0, top: 416 }, width: 390, height: 800 });
  assert.equal(inset.bottom, 384);
  assert.equal(inset.right, 0);
});

test('the mood line at the top counts as covered, also when the chat is collapsed', () => {
  assert.equal(insetFor({ mode: 'sheet', collapsed: false, rect: { left: 0, top: 416 }, width: 390, height: 800, top: 58.4 }).top, 58);
  assert.equal(insetFor({ mode: 'panel', collapsed: true, rect: null, width: 1440, height: 900, top: 58 }).top, 58);
});

test('a collapsed chat covers nothing', () => {
  assert.equal(insetFor({ mode: 'panel', collapsed: true, rect: { left: 1008, top: 0 }, width: 1440, height: 900 }).right, 0);
  assert.equal(insetFor({ mode: 'sheet', collapsed: true, rect: { left: 0, top: 400 }, width: 390, height: 800 }).bottom, 0);
});

test('a panel that is not measured yet or sticks out never gives negative values', () => {
  assert.equal(insetFor({ mode: 'panel', collapsed: false, rect: null, width: 1440, height: 900 }).right, 0);
  assert.equal(insetFor({ mode: 'panel', collapsed: false, rect: { left: 2000, top: 0 }, width: 1440, height: 900 }).right, 0);
});

test('caption text is plain', () => {
  assert.equal(captionText('Hello **world**, see [this](https://x.org).\n\n- one\n- two'), 'Hello world, see this. one two');
  assert.equal(captionText('```js\ncode()\n```\nAfter'), 'After');
  assert.equal(captionText(''), '');
  assert.equal(captionText(null), '');
});

test('a long caption shows the end of the answer', () => {
  const long = Array.from({ length: 60 }, (_, i) => `word${i}`).join(' ');
  const caption = captionText(long, 100);
  assert.ok(caption.startsWith('… '));
  assert.ok(caption.endsWith('word59'));
  assert.ok(caption.length <= 105);
});
