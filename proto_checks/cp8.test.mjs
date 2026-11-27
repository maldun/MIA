// PROTOTYPE CP8 checks (node --test): the working copy and its changes (FR-68), the form for the known fields (FR-92), the editing panel as text and inputs only
import test from 'node:test';
import assert from 'node:assert/strict';
import { nameProblem, nextConnectionId, addStep, removeStep, changeStep, addConnection, removeConnection, changeConnection, formFor, applyForm } from '../graph_app_v2/edit-model.js';
import { renderStepEditor, renderConnectionEditor } from '../graph_app_v2/edit-panel.js';
import { readFileSync } from 'node:fs';

// round 05 CP21: the editor gets the workflow profile from the backend's kinds answer (kept equal to GET /api/v2/kinds by cp21_check.py)
const W = JSON.parse(readFileSync(new URL('./kinds_answer.json', import.meta.url))).kinds.workflow;

const base = { nodes: [{ id: 'in', data: { type: 'data', value: 'x' } }, { id: 'step', data: { type: 'transform', toolbox_id: 'check.number' } }, { id: 'out', data: { type: 'data' } }],
  edges: [{ id: 'e1', from: 'in', to: 'step', data: {} }, { id: 'e2', from: 'step', to: 'out', data: {} }] };
const frozen = JSON.stringify(base);

test('FR-68: a new step of each kind starts with what its kind needs, and the stored graph is not touched', () => {
  for (const [kind, shape] of [['data', { type: 'data' }], ['transform', { type: 'transform', toolbox_id: '' }], ['master', { type: 'master', toolbox_id: '', stop: { max_repetitions: 1 } }]]) {
    const r = addStep(base, 'new', kind, W);
    assert.equal(r.error, null);
    assert.deepEqual(r.graph.nodes.at(-1), { id: 'new', data: shape });
  }
  assert.equal(JSON.stringify(base), frozen);
});

test('FR-68: a name that is empty, has a slash or is used is refused with the reason', () => {
  assert.match(addStep(base, '', 'data', W).error, /empty/);
  assert.match(addStep(base, 'a/b', 'data', W).error, /slash/);
  assert.match(addStep(base, 'step', 'data', W).error, /exists/);
  assert.match(addStep(base, 'ok', 'wizard', W).error, /Unknown kind/);
  assert.equal(nameProblem(base, 'fresh'), null);
});

test('FR-68: removing a step takes its connections with it; a connection can be added, changed and removed', () => {
  const less = removeStep(base, 'step');
  assert.deepEqual(less.nodes.map((n) => n.id), ['in', 'out']);
  assert.deepEqual(less.edges, []);
  const more = addConnection(base, 'in', 'out');
  assert.equal(more.error, null);
  assert.deepEqual(more.graph.edges.at(-1), { id: 'e3', from: 'in', to: 'out', data: {} });
  assert.equal(nextConnectionId(more.graph), 'e4');
  assert.match(addConnection(base, 'in', 'nowhere').error, /Both ends/);
  const role = changeConnection(more.graph, 'e3', { role: 'order', as: 'x' }, W);
  assert.deepEqual(role.graph.edges.at(-1).data, { role: 'order', as: 'x' });
  assert.deepEqual(changeConnection(role.graph, 'e3', { role: '', as: '' }, W).graph.edges.at(-1).data, {});
  assert.deepEqual(removeConnection(more.graph, 'e3').edges.map((e) => e.id), ['e1', 'e2']);
  assert.match(changeConnection(base, 'e9', {}, W).error, /no connection/);
});

test('FR-92: the form shows the known fields of each kind and the rest as text', () => {
  assert.deepEqual(formFor(base.nodes[0], W).fields.map((f) => f.name), ['value', 'parameters']);
  assert.deepEqual(formFor(base.nodes[1], W).fields.map((f) => f.name), ['toolbox_id']);
  const master = { id: 'm', data: { type: 'master', toolbox_id: 'control.loop', stop: { max_repetitions: 3 }, note: 'kept', extra: { a: 1 } } };
  const f = formFor(master, W);
  assert.deepEqual(f.fields.map((x) => x.name), ['toolbox_id', 'stop.max_repetitions', 'stop.max_seconds']);
  assert.deepEqual(JSON.parse(f.other), { note: 'kept', extra: { a: 1 } });
});

test('FR-92: applying the form gives the stored fields; a value that does not fit is refused with the reason, nothing is changed', () => {
  const ok = applyForm(base.nodes[1], { toolbox_id: ' check.date_claim ' }, '', W);
  assert.deepEqual(ok, { data: { type: 'transform', toolbox_id: 'check.date_claim' }, errors: {} });
  assert.deepEqual(applyForm(base.nodes[1], { toolbox_id: '' }, '', W).errors, { toolbox_id: 'A processing step needs a tool.' });
  const d = applyForm(base.nodes[0], { value: '{"a": [1, 2]}', parameters: '{"language": "python"}' }, '', W);
  assert.deepEqual(d.data, { type: 'data', value: { a: [1, 2] }, parameters: { language: 'python' } });
  assert.equal(applyForm(base.nodes[0], { value: '{bad', parameters: '[1]' }, '', W).errors.value, 'This is not valid JSON.');
  assert.equal(applyForm(base.nodes[0], { value: '', parameters: '[1]' }, '', W).errors.parameters, 'This must be a JSON object.');
  const m = { id: 'm', data: { type: 'master', toolbox_id: 'control.loop', stop: { max_repetitions: 2 } } };
  assert.deepEqual(applyForm(m, { toolbox_id: 'control.loop', 'stop.max_repetitions': '3', 'stop.max_seconds': '' }, '', W).data.stop, { max_repetitions: 3 });
  assert.equal(applyForm(m, { toolbox_id: 'control.loop', 'stop.max_repetitions': '1.5', 'stop.max_seconds': '' }, '', W).errors['stop.max_repetitions'], 'A whole number from 1.');
  assert.equal(applyForm(m, { toolbox_id: 'control.loop', 'stop.max_repetitions': '', 'stop.max_seconds': '-1' }, '', W).errors['stop.max_seconds'], 'A number above 0.');
  assert.match(applyForm(m, { toolbox_id: 'control.loop', 'stop.max_repetitions': '', 'stop.max_seconds': '' }, '', W).errors['stop.max_repetitions'], /needs a limit/);
});

test('FR-92: other fields as JSON text join the stored fields; a field the form sets cannot be overridden there', () => {
  const r = applyForm(base.nodes[1], { toolbox_id: 't' }, '{"note": "x"}', W);
  assert.deepEqual(r.data, { type: 'transform', toolbox_id: 't', note: 'x' });
  assert.match(applyForm(base.nodes[1], { toolbox_id: 't' }, '{"toolbox_id": "evil"}', W).errors.other, /set by the form/);
  assert.equal(applyForm(base.nodes[1], { toolbox_id: 't' }, '[1]', W).errors.other, 'This must be a JSON object.');
});

test('FR-92: the tool is chosen from a searchable list of the toolbox entries with trust and lifecycle, like the list of graphs; no dropdown', () => {
  const doc = fakeDoc2(), box = doc.createElement('div');
  const tools = [{ id: 'check.number', trust: 'trusted', lifecycle: 'tested', controller: false }, { id: 'check.date_claim', trust: 'trusted', lifecycle: 'tested', controller: false },
                 { id: 'code.tally', trust: 'trusted', lifecycle: 'draft', controller: false }, { id: 'control.loop', trust: 'trusted', lifecycle: 'tested', controller: true }];
  const step = { id: 's', data: { type: 'transform', toolbox_id: 'tool.v4' } };
  const parts = renderStepEditor(doc, box, step, { onApply() {}, onRemove() {}, tools, profile: W });
  const picker = parts.inputs.toolbox_id;
  assert.ok(!all(box).some((e) => e.tag === 'select'));                                               // no dropdown anywhere
  assert.equal(picker.search.attrs.type, 'search');
  assert.deepEqual(picker.list.children.map((li) => li.textContent), ['tool.v4  (not in the toolbox)', 'check.number  (trusted, tested)', 'check.date_claim  (trusted, tested)', 'code.tally  (trusted, draft)']);
  assert.ok(all(box).some((e) => e.textContent === 'Tool: tool.v4  (not in the toolbox)'));
  assert.equal(picker.value, 'tool.v4');
  picker.search.value = 'check'; picker.search.listeners.input();
  assert.deepEqual(picker.list.children.map((li) => li.textContent.split('  ')[0]), ['check.number', 'check.date_claim']);
  picker.search.value = 'date claim'.replace(' ', '_'); picker.search.listeners.input();
  assert.deepEqual(picker.list.children.map((li) => li.textContent.split('  ')[0]), ['check.date_claim']);
  picker.list.children[0].listeners.click();
  assert.equal(picker.value, 'check.date_claim');
  assert.ok(all(box).some((e) => e.textContent === 'Tool: check.date_claim  (trusted, tested)'));
  picker.search.value = 'tally'; picker.search.listeners.input();
  picker.list.children[0].listeners.keydown({ key: 'Enter', preventDefault() {} });
  assert.equal(picker.value, 'code.tally');
  picker.search.value = 'zzz'; picker.search.listeners.input();
  assert.deepEqual(picker.list.children, []);
});

test('FR-92: a loop-controlling step is offered only the controllers; a new step starts with no tool and Apply refuses it', () => {
  const doc = fakeDoc2(), box = doc.createElement('div'), got = [];
  const tools = [{ id: 'check.number', trust: 'trusted', lifecycle: 'tested', controller: false }, { id: 'control.loop', trust: 'trusted', lifecycle: 'tested', controller: true }];
  const m = renderStepEditor(doc, box, { id: 'm', data: { type: 'master', toolbox_id: 'control.loop', stop: { max_repetitions: 2 } } }, { onApply() {}, onRemove() {}, tools, profile: W });
  assert.deepEqual(m.inputs.toolbox_id.list.children.map((li) => li.textContent.split('  ')[0]), ['control.loop']);
  const n = renderStepEditor(doc, box, { id: 'n', data: { type: 'transform', toolbox_id: '' } }, { onApply: (r) => got.push(r), onRemove() {}, tools, profile: W });
  assert.ok(all(box).some((e) => e.textContent === 'Tool: (none chosen yet)'));
  n.apply.listeners.click();
  assert.deepEqual(got[0].errors, { toolbox_id: 'A processing step needs a tool.' });
  n.inputs.toolbox_id.list.children[0].listeners.click();
  n.apply.listeners.click();
  assert.deepEqual(got[1], { data: { type: 'transform', toolbox_id: 'check.number' }, errors: {} });
});

function fakeDoc2() {
  const make = (tag) => ({ tag, children: [], attrs: {}, _text: '', value: '', listeners: {},
    get textContent() { return this._text; }, set textContent(v) { this._text = String(v); },
    append(...c) { this.children.push(...c); }, replaceChildren(...c) { this.children = c; }, setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(t, f) { this.listeners[t] = f; } });
  return { createElement: make };
}

function fakeDoc() {
  const make = (tag) => ({ tag, children: [], attrs: {}, _text: '', value: '', listeners: {},
    get textContent() { return this._text; }, set textContent(v) { this._text = String(v); },
    set innerHTML(v) { throw new Error('innerHTML used'); },
    append(...c) { this.children.push(...c); }, replaceChildren(...c) { this.children = c; }, setAttribute(k, v) { this.attrs[k] = v; }, addEventListener(t, f) { this.listeners[t] = f; } });
  return { createElement: make };
}
const all = (e) => [e, ...e.children.flatMap(all)];

test('FR-92: the step editor is built from text and inputs only; hostile text stays text; Apply hands the new content on', () => {
  const doc = fakeDoc(), box = doc.createElement('div'), got = [];
  const step = { id: '<img src=x onerror=alert(1)>', data: { type: 'transform', toolbox_id: '<b>evil</b>' } };
  const parts = renderStepEditor(doc, box, step, { onApply: (r) => got.push(r), onRemove: () => got.push('removed'), profile: W });
  assert.ok(all(box).some((e) => e.textContent.includes('<img src=x onerror=alert(1)>')));
  assert.ok(all(box).every((e) => ['div', 'h3', 'p', 'label', 'span', 'input', 'textarea', 'button'].includes(e.tag)));
  assert.equal(parts.inputs.toolbox_id.value, '<b>evil</b>');
  parts.inputs.toolbox_id.value = 'check.number';
  parts.apply.listeners.click();
  assert.deepEqual(got[0], { data: { type: 'transform', toolbox_id: 'check.number' }, errors: {} });
  parts.remove.listeners.click();
  assert.equal(got[1], 'removed');
  const shown = renderStepEditor(doc, box, step, { onApply() {}, onRemove() {}, errors: { toolbox_id: 'A processing step needs a tool.' }, profile: W });
  assert.ok(all(box).some((e) => e.textContent === 'A processing step needs a tool.' && e.attrs.role === 'alert'));
  assert.ok(shown.apply);
});

test('FR-68: the connection editor hands on the role and the name', () => {
  const doc = fakeDoc(), box = doc.createElement('div'), got = [];
  const parts = renderConnectionEditor(doc, box, { id: 'e1', from: 'a', to: 'b', data: { role: 'code' } }, { onApply: (v) => got.push(v), onRemove() {}, profile: W });
  assert.equal(parts.role.value, 'code');
  parts.role.value = 'settings'; parts.as.value = 'cfg';
  parts.apply.listeners.click();
  assert.deepEqual(got[0], { role: 'settings', as: 'cfg' });
});
