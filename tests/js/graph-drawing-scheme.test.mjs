// The drawing on vis-network (graph_app/drawing.js) when the colour scheme changes: V-2 of the G-V4.VIEW verification (D-501).
// A recording vis stand-in replaces the vendored library. Run: node --test tests/js/graph-drawing-scheme.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { visDrawing } from '../../graph_app/drawing.js';

class DataSet {
  constructor(items = []) { this.items = new Map(items.map((i) => [i.id, { ...i }])); }
  update(change) { for (const c of [change].flat()) this.items.set(c.id, { ...this.items.get(c.id), ...c }); }
  get(id) { return id === undefined ? [...this.items.values()] : this.items.get(id); }
}

/** a vis stand-in that records setData and setOptions and answers positions from its node data */
function fakeVis() {
  const record = { setData: 0, options: [], handlers: {}, network: null };
  class Network {
    constructor(container, data) { this.data = data; record.network = this; }
    on(name, fn) { record.handlers[name] = fn; }
    setOptions(o) { record.options.push(o); }
    setData(data) { record.setData += 1; this.data = data; }
    getPosition(id) { const n = this.data.nodes.get(id); return { x: n.x, y: n.y }; }
    getPositions() { return Object.fromEntries(this.data.nodes.get().map((n) => [n.id, { x: n.x, y: n.y }])); }
  }
  return { vis: { DataSet, Network }, record };
}

/** a page whose CSS colours follow `scheme.colour`, and a dark-mode query whose change listener the test fires */
function fakePage(scheme) {
  globalThis.getComputedStyle = () => ({ getPropertyValue: (prop) => (prop === 'color' ? scheme.colour : 'sans-serif') });
  const doc = { body: { append() {} }, createElement: () => ({ style: { setProperty() {} }, remove() {} }) };
  const media = { listener: null };
  const win = { matchMedia: () => ({ addEventListener: (type, fn) => { media.listener = fn; } }), setTimeout: (fn) => fn() };
  return { container: { ownerDocument: doc }, win, media };
}

test('V-2, REQ-GA-016, REQ-GA-032: a scheme change re-colours the shown graph and keeps a dropped step where it was dropped', () => {
  // Example: a, b drawn and settled; a dropped at (500, 7); dark -> light: no second setData, a still at (500, 7), its label in the new colour.
  // Given a drawn and settled graph with step a dropped
  const scheme = { colour: 'rgb(230, 230, 230)' };
  const { container, win, media } = fakePage(scheme);
  const { vis, record } = fakeVis();
  const drawing = visDrawing(container, vis, win);
  drawing.show({ nodes: [{ id: 'a', label: 'a', shape: 'box', marks: [] }, { id: 'b', label: 'b', shape: 'hexagon', marks: [] }],
    edges: [{ id: 'e', from: 'a', to: 'b' }] }, { physics: true, layout: 'free', solver: 'barnesHut', seed: 1, edges: 'rounded' });
  record.handlers.stabilizationIterationsDone();
  record.network.data.nodes.update({ id: 'a', x: 500, y: 7 });
  record.handlers.dragEnd({ nodes: ['a'] });
  // When the colour scheme changes
  scheme.colour = 'rgb(20, 20, 20)';
  media.listener();
  // Then the graph was not set again, a kept its place, and the labels and connections take the new colour
  const a = record.network.data.nodes.get('a');
  assert.equal(record.setData, 1);
  assert.deepEqual([a.x, a.y, a.fixed], [500, 7, true]);
  assert.equal(a.font.color, 'rgb(20, 20, 20)');
  assert.equal(record.options.at(-1).edges.color.color, 'rgb(20, 20, 20)');
  assert.ok(!record.options.slice(2).some((o) => o.physics?.enabled), 'the solver stays off');
});
