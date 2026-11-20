// PROTOTYPE CP12 checks (node --test): playback of recorded changes (FR-78), the comparison of two versions (FR-79)
import test from 'node:test';
import assert from 'node:assert/strict';
import { applyChange, states, sameGraph, canonical, stepNote } from '../graph_app_v2/replay.js';
import { compareView, markText, compareNote } from '../graph_app_v2/compare.js';
import { diffChanges } from '../graph_app_v2/change-log.js';

const v1 = { nodes: [{ id: 'in', data: { type: 'data', value: 'x' } }, { id: 'step', data: { type: 'transform', toolbox_id: 'check.number' } }, { id: 'out', data: { type: 'data' } }],
  edges: [{ id: 'e1', from: 'in', to: 'step', data: {} }, { id: 'e2', from: 'step', to: 'out', data: {} }] };
const entries = [
  { op: 'add_step', target: 'n', before: null, after: { type: 'data', value: 'new' } },
  { op: 'add_connection', target: 'e3', before: null, after: { from: 'n', to: 'step', data: { role: 'order' } } },
  { op: 'change_step', target: 'step', before: v1.nodes[1].data, after: { type: 'transform', toolbox_id: 'check.claim' } },
  { op: 'remove_connection', target: 'e2', before: { from: 'step', to: 'out', data: {} }, after: null },
  { op: 'remove_step', target: 'out', before: { type: 'data' }, after: null, connections: [] },
];
const saved = { nodes: [{ id: 'in', data: { type: 'data', value: 'x' } }, { id: 'step', data: { type: 'transform', toolbox_id: 'check.claim' } }, { id: 'n', data: { type: 'data', value: 'new' } }],
  edges: [{ id: 'e1', from: 'in', to: 'step', data: {} }, { id: 'e3', from: 'n', to: 'step', data: { role: 'order' } }] };

test('FR-78: playing the entries on the starting version gives the saved version, and the starting version is not touched', () => {
  const frozen = JSON.stringify(v1);
  const all = states(v1, entries);
  assert.equal(all.length, entries.length + 1);
  assert.ok(sameGraph(all.at(-1), saved));
  assert.equal(JSON.stringify(v1), frozen);
  assert.ok(sameGraph(all[0], v1));
});

test('FR-78: every position shows what the changes up to there made; stepping back gives the earlier picture again', () => {
  const all = states(v1, entries);
  assert.deepEqual(all[1].nodes.map((n) => n.id), ['in', 'step', 'out', 'n']);
  assert.equal(all[3].nodes.find((n) => n.id === 'step').data.toolbox_id, 'check.claim');
  assert.ok(!all[4].edges.some((e) => e.id === 'e2'));
  assert.ok(sameGraph(states(v1, entries.slice(0, 2)).at(-1), all[2]));              // forward and back give the same pictures
});

test('FR-78: the end says whether the result is identical to the saved version', () => {
  assert.match(stepNote(0, entries, true), /Start/);
  assert.equal(stepNote(2, entries, true), 'Change 2 of 5');
  assert.match(stepNote(5, entries, true), /identical to the saved version/);
  assert.match(stepNote(5, entries, false), /NOT identical/);
});

test('FR-78: a change that does not start from this graph is told, not guessed', () => {
  assert.throws(() => applyChange(v1, { op: 'remove_step', target: 'ghost' }), /no step ghost/);
  assert.throws(() => applyChange(v1, { op: 'add_step', target: 'in', after: {} }), /exists/);
  assert.throws(() => applyChange(v1, { op: 'restore', target: 1 }), /needs the earlier version/);
  assert.ok(sameGraph(applyChange(saved, { op: 'restore', target: 1 }, () => v1), v1));
});

test('FR-78: the order of steps and of fields does not matter for "identical"', () => {
  const shuffled = { nodes: [...saved.nodes].reverse(), edges: [...saved.edges].reverse() };
  assert.ok(sameGraph(saved, shuffled));
  assert.equal(canonical({ nodes: [{ id: 'a', data: { b: 1, a: 2 } }], edges: [] }), canonical({ nodes: [{ id: 'a', data: { a: 2, b: 1 } }], edges: [] }));
});

test('FR-79: the added, removed and changed steps and connections are listed with old and new content and marked differently', () => {
  const view = compareView(v1, saved);
  assert.deepEqual(view.marks, { n: 'added', step: 'changed', out: 'removed' });
  assert.deepEqual(view.edgeMarks, { e3: 'added', e2: 'removed' });
  assert.equal(view.graph.nodes.length, 4);                                              // the removed step is still drawn
  assert.ok(view.lines.some((l) => /changed step "step": toolbox_id: "check.number" → "check.claim"/.test(l)));
  assert.ok(view.lines.some((l) => /added step "n"/.test(l)) && view.lines.some((l) => /removed step "out"/.test(l)) && view.lines.some((l) => /added connection "e3"/.test(l)));
  assert.deepEqual([markText('added'), markText('removed'), markText('changed'), markText(undefined)], ['[added]', '[removed]', '[changed]', '']);
});

test('FR-79: two equal versions say so; a changed connection is listed with both ends', () => {
  const same = compareView(v1, v1);
  assert.equal(same.none, true);
  assert.match(compareNote(1, 1, same), /same steps and connections/);
  const moved = { ...v1, edges: [{ id: 'e1', from: 'in', to: 'out', data: {} }, v1.edges[1]] };
  const view = compareView(v1, moved);
  assert.deepEqual(view.edgeMarks, { e1: 'changed' });
  assert.match(view.lines[0], /changed connection "e1": in → step became in → out/);
  assert.match(compareNote(1, 2, view), /Version 1 compared with version 2: 1 difference/);
});

test('FR-79: the comparison lists the same differences as the changes that the record would hold', () => {
  assert.equal(compareView(v1, saved).lines.length, diffChanges(v1, saved).length);
});
