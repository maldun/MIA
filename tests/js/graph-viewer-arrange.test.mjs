// The arrangement and the settings in the graph viewer (graph_app/viewer.js, REQ-GA-030 to 035): drag, settings place, layered reset.
// Run: node --test tests/js/graph-viewer-arrange.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument } from './fake-dom.mjs';
import { createViewer } from '../../graph_app/viewer.js';

const GRAPH = { graph: { id: 'g', nodes: [{ id: 'a', data: { type: 'data' } }, { id: 'b', data: { type: 'data' } }], edges: [{ id: 'e1', from: 'a', to: 'b' }] },
  version: 1, current: 1, author: 'anna', time: 't', problems: [], steps: {} };

function page() {
  const doc = installDocument();
  const root = doc.createElement('div');
  doc.body.append(root);
  const rec = { shows: [], options: [], dragEnd: null };
  const makeDrawing = () => ({ show: (data, options) => rec.shows.push({ data, options }), setOptions: (o) => rec.options.push(o), positions: () => ({}),
    onDragEnd: (fn) => { rec.dragEnd = fn; }, onStabilized() {} });
  const writes = [];
  const storage = { getItem: () => null, setItem: (k, v) => writes.push([k, v]) };
  const api = { me: async () => ({}), store: async () => ({ store: 'files', reachable: true }), listGraphs: async () => [],
    readGraph: async () => GRAPH, readArrangement: async () => ({ positions: null }) };
  return { root, rec, writes, viewer: createViewer({ document: doc, root, api, storage, makeDrawing }) };
}

test('REQ-GA-032: a dragged step is held where it was dropped while its graph stays open, also when it is read again', async () => {
  // Example: drag a to 100, 50 -> the next picture of g (opened again) holds a at 100, 50; nothing is written to the API.
  // Given g opened
  const { rec, viewer } = page();
  await viewer.start();
  await viewer.open('g');
  // When a is dragged and g is opened again
  rec.dragEnd({ id: 'a', x: 100, y: 50 });
  await viewer.open('g');
  // Then a is held at its new place
  const a = rec.shows.at(-1).data.nodes.find((n) => n.id === 'a');
  assert.deepEqual([a.x, a.y, a.fixed], [100, 50, true]);
});

test('REQ-GA-034: the settings place offers edges and arrangement; a change reaches the drawing at once and is kept', async () => {
  // Example: #settings-open shows the selects; edges straight -> setOptions {edges: straight}; arrangement off -> {physics: false}; both written.
  // Given g opened
  const { root, rec, writes, viewer } = page();
  await viewer.start();
  await viewer.open('g');
  // When the settings are opened and both selects changed
  root.querySelector('#settings-open').click();
  const edges = root.querySelector('[data-setting=edges]');
  const arrangement = root.querySelector('[data-setting=arrangement]');
  const open = root.querySelector('[data-settings]').hidden;
  edges.value = 'straight';
  edges.dispatchEvent({ type: 'change' });
  arrangement.value = 'off';
  arrangement.dispatchEvent({ type: 'change' });
  // Then the place was shown, the drawing got both options without a new picture, and the settings were written
  assert.equal(open, false);
  assert.deepEqual([rec.options.at(-1).edges, rec.options.at(-1).physics], ['straight', false]);
  assert.equal(rec.shows.length, 1);
  assert.deepEqual(JSON.parse(writes.at(-1)[1]), { edges: 'straight', arrangement: 'off' });
});

test('REQ-GA-033: the layered reset draws levels and lets go of the moved places', async () => {
  // Example: a dragged, then layered() -> a level 0, b level 1, no fixed place; layout layered; the button does the same.
  // Given g opened and a dragged
  const { root, rec, viewer } = page();
  await viewer.start();
  await viewer.open('g');
  rec.dragEnd({ id: 'a', x: 100, y: 50 });
  // When the layered reset is asked for, by the controller and by its button
  await viewer.layered();
  const byCall = rec.shows.at(-1);
  root.querySelector('#layered-reset').click();
  // Then the picture has levels, layout layered, and no held place
  assert.deepEqual(byCall.data.nodes.map((n) => [n.id, n.level, n.fixed]), [['a', 0, undefined], ['b', 1, undefined]]);
  assert.equal(byCall.options.layout, 'layered');
  assert.equal(rec.shows.length, 3);
});
