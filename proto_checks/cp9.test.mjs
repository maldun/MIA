// PROTOTYPE CP9 checks (node --test): undo and redo (FR-91), and what the owner is told about the live store (FR-95)
import test from 'node:test';
import assert from 'node:assert/strict';
import * as h from '../graph_app_v2/undo-stack.js';
import { storeNote, canEdit } from '../graph_app_v2/store-note.js';

test('FR-91: undo goes back one change at a time, redo forward again, nothing is lost on the way', () => {
  let s = h.create('g0');
  assert.deepEqual([h.canUndo(s), h.canRedo(s)], [false, false]);
  s = h.push(s, 'g1'); s = h.push(s, 'g2'); s = h.push(s, 'g3');
  assert.equal(s.present, 'g3');
  s = h.undo(s); s = h.undo(s);
  assert.equal(s.present, 'g1');
  assert.deepEqual([h.canUndo(s), h.canRedo(s)], [true, true]);
  s = h.redo(s);
  assert.equal(s.present, 'g2');
  assert.equal(h.note(s), '2 change(s) to undo, 1 to redo');
});

test('FR-91: a new change after an undo drops what could have been redone; undo and redo at the ends do nothing', () => {
  let s = h.push(h.push(h.create('a'), 'b'), 'c');
  s = h.undo(s);
  s = h.push(s, 'x');
  assert.equal(s.present, 'x');
  assert.equal(h.canRedo(s), false);
  assert.equal(h.redo(s), s);
  const start = h.create('a');
  assert.equal(h.undo(start), start);
});

test('FR-91: the session is only a list of working copies: the earlier ones are untouched when a later one is made', () => {
  const g0 = { nodes: [1] };
  let s = h.create(g0);
  s = h.push(s, { nodes: [1, 2] });
  assert.deepEqual(h.undo(s).present, { nodes: [1] });
  assert.equal(h.undo(s).present, g0);
});

test('FR-95: the owner is told whether the live store is reached and how far the copy is behind', () => {
  assert.equal(storeNote(null), '');
  assert.equal(storeNote({ split: false, live: 'reachable', lag: 0 }), '');
  assert.match(storeNote({ split: true, live: 'reachable', lag: 0 }), /copy is up to date/);
  assert.match(storeNote({ split: true, live: 'reachable', lag: 3 }), /behind by 3 version\(s\)/);
  assert.match(storeNote({ split: true, live: 'unreachable', lag: null }), /NOT REACHABLE.*changing is not possible/);
});

test('FR-95: the editor is allowed with one store, or when the live store is reachable, and not otherwise', () => {
  assert.equal(canEdit(null), true);
  assert.equal(canEdit({ split: false, live: 'reachable' }), true);
  assert.equal(canEdit({ split: true, live: 'reachable' }), true);
  assert.equal(canEdit({ split: true, live: 'unreachable' }), false);
});
