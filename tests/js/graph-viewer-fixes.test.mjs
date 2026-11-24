// Fixes after Verify of G-V4.VIEW (D-501) in graph_app/viewer.js: V-1 (keys in a real HTMLCollection), V-8 (a session ending with a graph
// open). Run: node --test tests/js/graph-viewer-fixes.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, flush } from './fake-dom.mjs';
import { createViewer } from '../../graph_app/viewer.js';

const LIST = [{ id: 'a', kind: 'workflow', version: 1, steps: 1, connections: 0, description: 'first' },
  { id: 'b', kind: 'workflow', version: 1, steps: 1, connections: 0, description: 'second' }];
const version = (n) => ({ graph: { id: 'cp2.multi', nodes: [{ id: 's', data: { type: 'data' } }], edges: [{ id: 'e', from: 's', to: 'gone', data: {} }] },
  version: n, current: 2, author: 'anna', time: `t${n}`, problems: [{ problem: 'missing_step', connection: 'e', step: 'gone', end: 'to' }], steps: {} });

function page(state = {}) {
  const doc = installDocument();
  const root = doc.createElement('div');
  doc.body.append(root);
  const reads = [];
  const fail = () => {
    if (state.gone) throw { status: 401, code: 'unauthenticated', detail: {} };
    if (state.unreachable) throw { status: 503, code: 'store_unreachable', detail: {} };
  };
  const api = { me: async () => { fail(); return { user: 'anna' }; }, store: async () => ({ store: 'database', reachable: !state.unreachable, shown: 'live' }),
    listGraphs: async () => { fail(); return LIST; }, readGraph: async (id, n) => { reads.push([id, n ?? null]); fail(); return version(n ?? 2); },
    readArrangement: async () => { fail(); return { positions: null }; },
    versions: async () => { fail(); return [{ version: 1, author: 'anna', time: 't1' }, { version: 2, author: 'anna', time: 't2' }]; } };
  const makeDrawing = () => ({ show() {}, setOptions() {}, positions: () => ({}), onDragEnd() {}, onStabilized() {} });
  return { doc, root, reads, viewer: createViewer({ document: doc, root, api, storage: null, makeDrawing }) };
}

/** what a browser hands out as `children`: indexable and iterable, but not an Array (no `filter`) */
function asHtmlCollection(element) {
  const real = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element), 'children').get;
  Object.defineProperty(element, 'children', { get() {
    const items = real.call(element);
    const collection = { length: items.length, item: (i) => items[i] ?? null, [Symbol.iterator]: () => items[Symbol.iterator]() };
    items.forEach((e, i) => { collection[i] = e; });
    return collection;
  } });
}

test('V-1, REQ-GA-019: the arrow keys move the focus when the list children are an HTMLCollection', async () => {
  // Example: children without filter; ArrowDown on a -> b focused, no exception.
  // Given the started page whose list hands out an HTMLCollection
  const { doc, root, viewer } = page();
  await viewer.start();
  const [a, b] = ['a', 'b'].map((id) => root.querySelector(`[data-graph-id="${id}"]`));
  asHtmlCollection(a.parentElement);
  // When ArrowDown is pressed on a
  a.dispatchEvent({ type: 'keydown', key: 'ArrowDown' });
  // Then b has the focus
  assert.equal(doc.activeElement, b);
});

test('V-8, REQ-GA-022: a session ending while a graph is open empties the left column and the history, and the buttons send nothing', async () => {
  // Example: cp2.multi open, step s selected, history open; 401 on the next read -> no problem, step, field or version left; previous reads nothing.
  // Given cp2.multi open with a step selected and its history shown
  const state = {};
  const { root, reads, viewer } = page(state);
  await viewer.start();
  await viewer.open('cp2.multi');
  await viewer.selectStep('s');
  await viewer.openHistory();
  // When the session ends and the owner asks for the previous version
  state.gone = true;
  await viewer.previous();
  const readsAfter = reads.length;
  await viewer.previous();
  await viewer.next();
  // Then nothing of the graph is left, the history buttons are off, and no further read was sent
  const left = root.querySelector('[data-area=left-column]');
  assert.equal(left.querySelectorAll('[data-problem]').length, 0);
  assert.equal(left.querySelectorAll('[data-step-id]').length, 0);
  assert.equal(left.querySelectorAll('[data-field]').length, 0);
  assert.equal(root.querySelectorAll('[data-version]').length, 0);
  assert.deepEqual(['#history-open', '#history-previous', '#history-next'].map((s) => root.querySelector(s).getAttribute('disabled')), ['', '', '']);
  assert.equal(reads.length, readsAfter);
  assert.ok(!reads.some(([id]) => id === null));
});
