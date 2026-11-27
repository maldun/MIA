// PROTOTYPE round 05 CP21 checks (node --test): the editor builds everything from the profile of the graph's kind (FR-92, D-403, D-404, D-602)
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { profileOf, nodeTypes, typeName, addStep, formFor, applyForm, addConnection, changeConnection } from '../graph_app_v2/edit-model.js';
import { renderStepEditor, renderConnectionEditor } from '../graph_app_v2/edit-panel.js';

const ANSWER = JSON.parse(readFileSync(new URL('./kinds_answer.json', import.meta.url)));

// a kind that exists nowhere in the program: if the editor handles it, the editor knows no kind itself
const DEMO = {
  editable: true, rules: [], runs: false,
  node_types: [{ type: 'note', name: 'note', start: { type: 'note', title: '' },
    fields: [{ name: 'title', label: 'title', input: 'text', required: true, message: 'A note needs a title.' },
             { name: 'weight.count', label: 'weight', input: 'number', above: 0, whole: true },
             { name: 'colour', label: 'colour', input: 'choice', options: ['', 'red', 'blue'] }] }],
  connection_fields: [{ name: 'relation', label: 'relation', input: 'choice', options: ['', 'cites', 'contradicts'] }],
};
const WITH_DEMO = { ...ANSWER, kinds: { ...ANSWER.kinds, demo: DEMO } };
const empty = { nodes: [], edges: [] };

test('D-404, D-602: a workflow graph is editable; a context graph and an unknown kind are not, and the reason is given', () => {
  assert.equal(profileOf(ANSWER, 'workflow').editable, true);
  assert.equal(profileOf(ANSWER, undefined).editable, true, 'no kind is a workflow graph (REQ-WFM-153)');
  const cx = profileOf(ANSWER, 'context');
  assert.equal(cx.editable, false);
  assert.match(cx.reason, /G-V4\.CONTEXT/);
  const unknown = profileOf(ANSWER, 'mystery');
  assert.equal(unknown.editable, false);
  assert.match(unknown.reason, /does not know .*\(mystery\)/);
});

test('FR-92: the types to add come from the profile, in its order and words', () => {
  assert.deepEqual(nodeTypes(profileOf(ANSWER, 'workflow').profile).map((t) => t.name), ['data step', 'processing step', 'loop-controlling step']);
  assert.deepEqual(nodeTypes(profileOf(ANSWER, 'context').profile), []);
});

test('FR-92 generality: a kind the program has never seen gets its start content, form, checks and connection fields from its profile alone', () => {
  const P = profileOf(WITH_DEMO, 'demo').profile;
  const added = addStep(empty, 'n1', 'note', P);
  assert.deepEqual(added.graph.nodes, [{ id: 'n1', data: { type: 'note', title: '' } }]);
  assert.equal(typeName(P, 'note'), 'note');
  assert.match(addStep(empty, 'x', 'data', P).error, /Unknown kind/, 'a workflow type is not offered in another kind');

  const step = { id: 'n1', data: { type: 'note', title: 'T', weight: { count: 2 }, colour: 'red', extra: [1] } };
  const form = formFor(step, P);
  assert.deepEqual(form.fields.map((f) => [f.name, f.value]), [['title', 'T'], ['weight.count', '2'], ['colour', 'red']]);
  assert.deepEqual(JSON.parse(form.other), { extra: [1] });

  assert.deepEqual(applyForm(step, { title: ' U ', 'weight.count': '3', colour: 'blue' }, form.other, P),
    { data: { type: 'note', title: 'U', weight: { count: 3 }, colour: 'blue', extra: [1] }, errors: {} });
  const bad = applyForm(step, { title: '', 'weight.count': '0', colour: 'green' }, '', P);
  assert.deepEqual(bad.errors, { title: 'A note needs a title.', 'weight.count': 'A whole number from 1.', colour: 'One of: red, blue.' });

  const linked = addConnection({ nodes: [{ id: 'a' }, { id: 'b' }], edges: [] }, 'a', 'b', { relation: 'cites' }, P);
  assert.deepEqual(linked.graph.edges[0].data, { relation: 'cites' });
  assert.match(addConnection({ nodes: [{ id: 'a' }, { id: 'b' }], edges: [] }, 'a', 'b', { relation: 'likes' }, P).error, /relation: One of: cites, contradicts/);
  assert.deepEqual(changeConnection(linked.graph, 'e1', { relation: '' }, P).graph.edges[0].data, {});
});

function fakeDoc() {
  const make = (tag) => ({ tag, children: [], attrs: {}, _text: '', value: '', listeners: {},
    get textContent() { return this._text; }, set textContent(v) { this._text = String(v); },
    set innerHTML(v) { throw new Error('innerHTML used'); },
    append(...c) { this.children.push(...c); }, replaceChildren(...c) { this.children = c; }, setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(t, f) { this.listeners[t] = f; } });
  return { createElement: make };
}
const all = (e) => [e, ...e.children.flatMap(all)];

test('FR-92 generality: the panel of another kind shows only that kind\'s words and controls, a fixed choice as a list', () => {
  const P = profileOf(WITH_DEMO, 'demo').profile;
  const doc = fakeDoc(), box = doc.createElement('div'), got = [];
  const parts = renderStepEditor(doc, box, { id: 'n1', data: { type: 'note', title: 'T', colour: 'red' } }, { onApply: (r) => got.push(r), onRemove() {}, profile: P });
  const words = all(box).map((e) => e.textContent).join(' | ');
  assert.doesNotMatch(words, /processing|loop-controlling|data step|tool/, 'no workflow word in the panel of another kind');
  assert.equal(parts.inputs.colour.tag, 'select');
  assert.deepEqual(parts.inputs.colour.children.map((o) => o.textContent), ['(none)', 'red', 'blue']);
  parts.inputs.title.value = 'New';
  parts.apply.listeners.click();
  assert.deepEqual(got[0], { data: { type: 'note', title: 'New', colour: 'red' }, errors: {} });

  const link = renderConnectionEditor(doc, box, { id: 'e1', from: 'a', to: 'b', data: { relation: 'cites', note: 'kept' } }, { onApply: (v) => got.push(v), onRemove() {}, profile: P });
  assert.deepEqual(Object.keys(link.inputs), ['relation']);
});
