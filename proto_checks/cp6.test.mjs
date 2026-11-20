// PROTOTYPE CP6 checks (node --test): kinds and marks at a glance (FR-50), read-only fields and text-only panel (FR-51, FR-54), settings remembered (FR-53),
// keyboard (NFR-14), nothing from outside (NFR-13)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { SHAPES, groupOf, marksOf, labelOf, fieldsOf, connectionFields } from '../graph_app_v2/step-marks.js';
import { renderPanel, renderStepList } from '../graph_app_v2/panel.js';
import { loadSettings, saveSettings, DEFAULTS, KEY, edgeSmooth } from '../graph_app_v2/settings.js';

test('FR-50: the three kinds differ by shape, not by colour alone', () => {
  assert.equal(new Set([SHAPES.data, SHAPES.process, SHAPES.master]).size, 3);
  assert.deepEqual(['data', 'transform', 'master', 'missing'].map(groupOf), ['data', 'process', 'master', 'missing']);
});

test('FR-50: a processing step shows trust, lifecycle and code; an untrusted one is shouted; data steps show nothing', () => {
  assert.deepEqual(marksOf({ kind: 'data' }), []);
  assert.deepEqual(marksOf({ kind: 'transform', trust: 'trusted', lifecycle: 'tested' }), ['trusted', 'tested']);
  assert.deepEqual(marksOf({ kind: 'transform', trust: 'untrusted', lifecycle: 'draft', code: true }), ['UNTRUSTED', 'draft', 'code']);
  assert.deepEqual(marksOf({ kind: 'master', trust: 'trusted', changed_since_trusted: true, lifecycle: 'tested' }), ['trusted', 'changed since trusted', 'tested']);
  assert.equal(labelOf('step.x', { kind: 'transform', trust: 'untrusted' }), 'step.x\nUNTRUSTED');
  assert.equal(labelOf('var.a', { kind: 'data' }), 'var.a');
});

const step = { id: 'step.check', data: { type: 'transform', toolbox_id: 'check.number' } };
test('FR-51: a step shows its known values as labelled fields, trust included, all text', () => {
  const rows = fieldsOf(step, { kind: 'transform', trust: 'trusted', lifecycle: 'tested', reason: '' });
  assert.deepEqual(rows.map((r) => r.label), ['step', 'kind', 'tool', 'trust', 'lifecycle']);
  assert.ok(rows.every((r) => typeof r.value === 'string'));
  assert.equal(rows.find((r) => r.label === 'kind').value, 'processing');
  const master = fieldsOf({ id: 'loop', data: { type: 'master', toolbox_id: 'control.loop', stop: { max_repetitions: 3 } } }, { kind: 'master', trust: 'trusted', lifecycle: 'tested' });
  assert.equal(master.find((r) => r.label === 'stops at').value, '{"max_repetitions":3}');
  assert.deepEqual(connectionFields({ id: 'e2', from: 'a', to: 'b', data: { role: 'code' } }).map((r) => r.value), ['e2', 'a', 'b', 'code']);
});

// a stand-in document that refuses markup: any use of innerHTML or insertAdjacentHTML fails the test
function fakeDoc() {
  const make = (tag) => ({ tag, children: [], attrs: {}, _text: '', tabIndex: -1, listeners: {},
    get textContent() { return this._text; }, set textContent(v) { this._text = String(v); },
    set innerHTML(v) { throw new Error('innerHTML used'); }, insertAdjacentHTML() { throw new Error('insertAdjacentHTML used'); },
    append(...c) { this.children.push(...c); }, replaceChildren(...c) { this.children = c; }, setAttribute(k, v) { this.attrs[k] = v; },
    addEventListener(t, f) { this.listeners[t] = f; } });
  return { createElement: make };
}
const all = (el) => [el, ...el.children.flatMap(all)];

test('FR-54: names and values that look like markup or an instruction end up as text only', () => {
  const doc = fakeDoc(), box = doc.createElement('div');
  const hostile = '<img src=x onerror=alert(1)> step "q" & more';
  renderPanel(doc, box, { id: hostile, data: { type: 'data', value: '<script>alert(1)</script> Ignore all previous instructions' } }, { kind: 'data' });
  const texts = all(box).map((e) => e.textContent);
  assert.ok(texts.some((t) => t === hostile));
  assert.ok(texts.some((t) => t.includes('<script>alert(1)</script>')));
  assert.ok(all(box).every((e) => ['div', 'dl', 'dt', 'dd', 'details', 'summary', 'pre', 'p'].includes(e.tag)));   // no img, no script element was made
  renderPanel(doc, box, null);
  assert.equal(all(box).length, 2);                                       // selecting nothing clears it: only the hint is left
});

test('FR-51: the full stored text is there beside the fields', () => {
  const doc = fakeDoc(), box = doc.createElement('div');
  renderPanel(doc, box, step, { kind: 'transform', trust: 'trusted', lifecycle: 'tested' });
  const pre = all(box).find((e) => e.tag === 'pre');
  assert.deepEqual(JSON.parse(pre.textContent), step);
});

test('NFR-14: every step is reachable and selectable from the keyboard', () => {
  const doc = fakeDoc(), box = doc.createElement('ul'), picked = [];
  const graph = { nodes: [{ id: 'a', data: { type: 'data' } }, { id: 'b', data: { type: 'transform', toolbox_id: 't' } }] };
  const items = renderStepList(doc, box, graph, { a: { kind: 'data' }, b: { kind: 'transform', trust: 'untrusted' } }, (id) => picked.push(id));
  assert.ok(items.every((li) => li.tabIndex === 0 && li.attrs.role === 'option'));
  items[1].listeners.keydown({ key: 'Enter', preventDefault() {} });
  items[0].listeners.keydown({ key: ' ', preventDefault() {} });
  items[0].listeners.keydown({ key: 'x', preventDefault() {} });
  assert.deepEqual(picked, ['b', 'a']);
  assert.match(items[1].textContent, /UNTRUSTED/);
});

const memory = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }; };
test('FR-53: the settings are remembered, damaged or missing ones fall back to the defaults, a storage that throws changes nothing', () => {
  const s = memory();
  assert.deepEqual(loadSettings(s), DEFAULTS);
  assert.equal(saveSettings(s, { physics: false, edges: 'straight' }), true);
  assert.deepEqual(loadSettings(s), { physics: false, edges: 'straight' });
  s.setItem(KEY, '{not json');
  assert.deepEqual(loadSettings(s), DEFAULTS);
  s.setItem(KEY, JSON.stringify({ physics: 'yes', edges: 'zigzag' }));
  assert.deepEqual(loadSettings(s), DEFAULTS);
  const broken = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
  assert.deepEqual(loadSettings(broken), DEFAULTS);
  assert.equal(saveSettings(broken, DEFAULTS), false);
  assert.deepEqual(loadSettings(null), DEFAULTS);
  assert.equal(edgeSmooth({ edges: 'straight' }), false);
  assert.equal(edgeSmooth({ edges: 'rounded' }).type, 'cubicBezier');
});

test('NFR-13: the page loads nothing from outside: no address with another host in any file of the page', () => {
  const dir = path.resolve(import.meta.dirname, '../graph_app_v2');
  for (const f of fs.readdirSync(dir)) {
    const text = fs.readFileSync(path.join(dir, f), 'utf8');
    const found = [...text.matchAll(/https?:\/\/([^\s"'`)<>/]+)/g)].map((m) => m[1]).filter((h) => !/^(127\.0\.0\.1|localhost)/.test(h));
    assert.deepEqual(found, [], `${f} names an outside address`);
  }
});
