// PROTOTYPE CP11 checks (node --test): the changes of an editing session as entries (FR-76), reasons (FR-77), how a version is explained
import test from 'node:test';
import assert from 'node:assert/strict';
import { diffChanges, sessionChanges, withReasons, changeKey, describeChange, explain } from '../graph_app_v2/change-log.js';
import * as hist from '../graph_app_v2/undo-stack.js';
import { addStep, removeStep, changeStep, addConnection, removeConnection } from '../graph_app_v2/edit-model.js';

const base = { nodes: [{ id: 'in', data: { type: 'data', value: 'x' } }, { id: 'step', data: { type: 'transform', toolbox_id: 'check.number' } }, { id: 'out', data: { type: 'data' } }],
  edges: [{ id: 'e1', from: 'in', to: 'step', data: {} }, { id: 'e2', from: 'step', to: 'out', data: {} }] };

test('FR-76: one action of the editor is one entry, with the value before and after', () => {
  const a = addStep(base, 'n', 'data').graph;
  assert.deepEqual(diffChanges(base, a), [{ op: 'add_step', target: 'n', before: null, after: { type: 'data' }, reason: null }]);
  const c = changeStep(a, 'step', { type: 'transform', toolbox_id: 'check.claim' }).graph;
  const [ch] = diffChanges(a, c);
  assert.deepEqual([ch.op, ch.before.toolbox_id, ch.after.toolbox_id], ['change_step', 'check.number', 'check.claim']);
  const r = removeStep(base, 'step');
  const [rm] = diffChanges(base, r);
  assert.equal(rm.op, 'remove_step');
  assert.deepEqual(rm.connections.map((x) => x.id), ['e1', 'e2']);                // the connections that went with the step are named in its entry
  assert.equal(diffChanges(base, r).length, 1);
  const withLink = addConnection(base, 'in', 'out').graph;
  assert.equal(diffChanges(base, withLink)[0].op, 'add_connection');
  assert.equal(diffChanges(withLink, removeConnection(withLink, 'e3'))[0].op, 'remove_connection');
});

test('FR-76: only the changes that would be kept are entries: undone changes are not', () => {
  let h = hist.create(base);
  h = hist.push(h, addStep(h.present, 'a', 'data').graph);
  h = hist.push(h, addStep(h.present, 'b', 'data').graph);
  h = hist.push(h, changeStep(h.present, 'step', { type: 'transform', toolbox_id: 'check.claim' }).graph);
  assert.equal(sessionChanges(h).length, 3);
  h = hist.undo(hist.undo(h));
  assert.deepEqual(sessionChanges(h).map((c) => c.target), ['a']);
  h = hist.redo(h);
  assert.deepEqual(sessionChanges(h).map((c) => c.target), ['a', 'b']);
  assert.deepEqual(sessionChanges(hist.create(base)), []);
});

test('FR-77: a reason typed for a change stays with that change, and a change without one has none', () => {
  let h = hist.create(base);
  h = hist.push(h, addStep(h.present, 'a', 'data').graph);
  h = hist.push(h, addStep(h.present, 'b', 'data').graph);
  const [first, second] = sessionChanges(h);
  const reasons = new Map([[changeKey(first), '  because the test needs it  ']]);
  assert.deepEqual(withReasons([first, second], reasons).map((c) => c.reason), ['because the test needs it', null]);
  h = hist.undo(h); h = hist.redo(h);
  assert.equal(changeKey(sessionChanges(h)[0]), changeKey(first));                // undo and redo keep the key, so the reason is still found
});

test('FR-76: an entry is described in words with the value before and after', () => {
  assert.equal(describeChange({ op: 'change_step', target: 's', before: { type: 'transform', toolbox_id: 'a' }, after: { type: 'transform', toolbox_id: 'b' } }), 'changed step "s": toolbox_id: "a" → "b"');
  assert.match(describeChange({ op: 'add_step', target: 'n', after: { type: 'data' }, note: 'copied from g: s' }), /added step "n" \(data\), copied from g: s/);
  assert.match(describeChange({ op: 'remove_step', target: 'n', before: { type: 'data' }, connections: [1, 2] }), /removed step "n" \(data\) with 2 connection/);
  assert.match(describeChange({ op: 'change_connection', target: 'e', before: { from: 'a', to: 'b', data: {} }, after: { from: 'a', to: 'c', data: { role: 'order' } } }), /a → b became a → c; role: \(nothing\) → "order"/);
  assert.match(describeChange({ op: 'restore', target: 2 }), /restored the content of version 2/);
});

test('FR-76, NFR-20: a version is explained by its entries with their reasons, or as made before the record', () => {
  const lines = explain({ version: 5, kind: 'editor', from_version: 4, author: 'owner', time: 't', entries: [{ n: 1, op: 'add_step', target: 'n', after: { type: 'data' }, reason: 'for the test' }, { n: 2, op: 'remove_connection', target: 'e1', before: { from: 'a', to: 'b' }, reason: null }] });
  assert.match(lines[0], /Version 5 started from version 4; kept by owner/);
  assert.match(lines[1], /^1\. added step "n" \(data\) - reason: for the test$/);
  assert.match(lines[2], /^2\. removed connection "e1": a → b - no reason given$/);
  assert.match(explain({ version: 1, kind: 'before_the_record', author: 'sample', time: 't', entries: [] })[0], /made before the record of changes existed/);
  assert.match(explain({ version: 2, kind: 'derived', from_version: 1, author: 'x', time: 't', entries: [] })[0], /worked out from the difference/);
  assert.deepEqual(explain(undefined), ['No record for this version.']);
});
