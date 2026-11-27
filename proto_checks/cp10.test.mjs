// PROTOTYPE CP10 checks (node --test): copying a step into another graph (FR-94) as a form of text and inputs only; the arrangement helpers stay as in CP7 (FR-74)
import test from 'node:test';
import assert from 'node:assert/strict';
import { copyTargets, copyMessage, renderCopyPanel } from '../graph_app_v2/copy-panel.js';
import { positionsOf, applyPositions } from '../graph_app_v2/arrangement.js';

const graphs = [
  { id: 'research', kind: 'workflow', version: 3, steps: 9, connections: 8, description: 'checks claims' },
  { id: 'chat.answer', kind: 'workflow', version: 1, steps: 4, connections: 3, description: 'answers' },
  { id: 'ctx.main', kind: 'context', version: 2, steps: 5, connections: 4, description: '' },
  { id: 'plan.b', kind: 'workflow', version: 1, steps: 2, connections: 1, description: 'second target' },   // round 05 CP23: a second workflow target, since ctx.main is no longer one
];

function fakeDoc() {
  const make = (tag) => ({ tag, children: [], attrs: {}, _text: '', value: '', listeners: {}, disabled: false,
    get textContent() { return this._text; }, set textContent(v) { this._text = String(v); },
    set innerHTML(v) { throw new Error('innerHTML used'); },
    append(...c) { this.children.push(...c); }, replaceChildren(...c) { this.children = c; }, setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(t, f) { this.listeners[t] = f; } });
  return { createElement: make };
}
const all = (e) => [e, ...e.children.flatMap(all)];

test('FR-94: the other graphs are offered, never the one the step is in, narrowed by what was typed', () => {
  // round 05 CP23: only graphs of the same kind (D-403, decided after round 02); ctx.main is a context graph and no longer offered
  assert.deepEqual(copyTargets(graphs, 'research', '').map((g) => g.id), ['chat.answer', 'plan.b']);
  assert.deepEqual(copyTargets(graphs, 'research', 'ctx').map((g) => g.id), []);
  assert.deepEqual(copyTargets(graphs, 'research', 'research'), []);
  assert.deepEqual(copyTargets(null, 'x', ''), []);
});

test('FR-94: the owner is told what happened, in words, for every answer', () => {
  assert.match(copyMessage(200, { step: 'check', version: 4, synced: true }, 'check', 'chat.answer'), /Copied "check" into chat.answer as "check".*version 4/);
  assert.match(copyMessage(200, { step: 'c2', version: 4, synced: false, sync_problem: 'x' }, 'check', 'g'), /copy could not be updated/);
  assert.match(copyMessage(409, { error: 'name_taken', name: 'check' }, 'check', 'g'), /already has a step named "check".*another name/);
  assert.match(copyMessage(422, { rules: [{ rule: 'adjacency', parts: ['a', 'b'] }] }, 'check', 'g'), /break a rule.*adjacency \(a, b\)/);
  assert.match(copyMessage(422, { error: 'same_graph' }, 'check', 'g'), /different graph/);
  assert.match(copyMessage(503, {}, 'check', 'g'), /live store cannot be reached/);
  assert.match(copyMessage(403, {}, 'check', 'g'), /Only the owner/);
  assert.match(copyMessage(500, { error: 'boom' }, 'check', 'g'), /not copied \(500 boom\)/);
});

test('FR-94: the form is text and inputs only, the button waits for a graph, and the request carries the chosen graph and the name', () => {
  const doc = fakeDoc(), box = doc.createElement('div'), got = [];
  const hostile = '<img src=x onerror=alert(1)>';
  const form = renderCopyPanel(doc, box, { id: hostile, data: { type: 'data' } }, graphs, 'research', { onCopy: (r) => got.push(r) });
  assert.equal(form.button.disabled, true);
  assert.equal(form.name.value, hostile);                                       // the name of the copy starts as the step's name, as text
  assert.equal(all(box).some((e) => e.tag === 'img'), false);
  assert.equal(form.list.children.length, 2);
  form.button.listeners.click();
  assert.deepEqual(got, []);                                                      // nothing chosen: nothing sent
  form.list.children[1].listeners.click();
  assert.equal(form.chosen, 'plan.b');
  assert.equal(form.button.disabled, false);
  form.name.value = '  copy  ';
  form.button.listeners.click();
  assert.deepEqual(got, [{ target: 'plan.b', name: 'copy' }]);
  form.search.value = 'chat'; form.search.listeners.input();
  assert.equal(form.list.children.length, 1);
});

test('FR-94: the list is reachable by keyboard (Enter and Space choose)', () => {
  const doc = fakeDoc(), box = doc.createElement('div');
  const form = renderCopyPanel(doc, box, { id: 's', data: { type: 'data' } }, graphs, 'research', { onCopy: () => {} });
  form.list.children[0].listeners.keydown({ key: ' ', preventDefault() {} });
  assert.equal(form.chosen, 'chat.answer');
  form.list.children[1].listeners.keydown({ key: 'Enter', preventDefault() {} });
  assert.equal(form.chosen, 'plan.b');
  assert.equal(form.list.children[0].attrs.tabindex, undefined);
});

test('FR-74: the places the editor saves are whole numbers, and a saved arrangement is used while the working copy has its own steps', () => {
  assert.deepEqual(positionsOf({ a: { x: 10.6, y: -3.2 } }), { a: { x: 11, y: -3 } });
  const placed = applyPositions([{ id: 'a' }, { id: 'new' }], { a: { x: 1, y: 2 } });
  assert.equal(placed.fixed, false);                                              // the new step has no place yet: the graph settles around the saved ones
  assert.deepEqual(placed.nodes[0], { id: 'a', x: 1, y: 2 });
});
