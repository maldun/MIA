// The left column and the history row of the graph viewer (graph_app/viewer.js, REQ-GA-036 to 041, 044) beyond the acceptance checks.
// Run: node --test tests/js/graph-viewer-history.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, flush } from './fake-dom.mjs';
import { createViewer } from '../../graph_app/viewer.js';

const version = (n) => ({ graph: { id: 'g', nodes: [{ id: 'a', data: { type: 'data' } }, { id: 'b', data: { type: 'transform', toolbox_id: `t${n}` } }],
  edges: [{ id: 'e1', from: 'a', to: 'b', data: {} }, { id: 'e2', from: 'b', to: 'gone', data: {} }] },
version: n, current: 2, author: n === 1 ? 'anna' : 'ben', time: `t${n}`, problems: [{ problem: 'missing_step', connection: 'e2', step: 'gone', end: 'to' }],
steps: { a: { kind: 'data' }, b: { kind: 'transform', trust: 'trusted', lifecycle: 'tested', reason: 'it is in the toolbox', code: false, changed_since_trusted: false } } });

function page() {
  const doc = installDocument();
  const root = doc.createElement('div');
  doc.body.append(root);
  const reads = [];
  const api = { me: async () => ({}), store: async () => ({ store: 'files', reachable: true }), listGraphs: async () => [],
    readGraph: async (id, n) => { reads.push(n ?? null); return version(n ?? 2); }, readArrangement: async () => ({ positions: null }),
    versions: async () => [{ version: 1, author: 'anna', time: 't1' }, { version: 2, author: 'ben', time: 't2' }] };
  const makeDrawing = () => ({ show() {}, setOptions() {}, positions: () => ({}), onDragEnd() {}, onStabilized() {} });
  return { doc, root, reads, viewer: createViewer({ document: doc, root, api, storage: null, makeDrawing }) };
}
const field = (root, name) => root.querySelector(`[data-area=left-column] [data-field="${name}"]`)?.textContent ?? null;

test('REQ-GA-041: the step list holds every drawn step; a click or Enter selects it', async () => {
  // Example: g -> a, b and the missing gone listed; click b -> toolbox ID t2; Enter on gone -> kind missing step.
  // Given g opened
  const { root, viewer } = page();
  await viewer.start();
  await viewer.open('g');
  // When b is clicked and Enter pressed on gone
  const ids = root.querySelectorAll('[data-step-id]').map((e) => e.dataset.stepId);
  root.querySelector('[data-step-id="b"]').click();
  await flush();
  const tool = field(root, 'toolbox_id');
  root.querySelector('[data-step-id="gone"]').dispatchEvent({ type: 'keydown', key: 'Enter' });
  await flush();
  // Then every drawn step is listed, and each selection fills the column
  assert.deepEqual(ids, ['a', 'b', 'gone']);
  assert.equal(tool, 'toolbox ID: t2');
  assert.equal(field(root, 'kind'), 'kind: missing step');
});

test('REQ-GA-036: an unknown ID selects nothing, and a new version empties the selection', async () => {
  // Example: selectStep('zz') -> no field; b selected, then version 1 shown -> no field.
  // Given g opened and b selected
  const { root, viewer } = page();
  await viewer.start();
  await viewer.open('g');
  await viewer.selectStep('zz');
  const unknown = root.querySelectorAll('[data-field]').length;
  await viewer.selectStep('b');
  // When version 1 is shown
  await viewer.openHistory();
  await viewer.showVersion(1);
  // Then neither left a field
  assert.equal(unknown, 0);
  assert.equal(root.querySelectorAll('[data-field]').length, 0);
});

test('REQ-GA-038 to 040: the buttons of the history row open it and step through it; the shown entry is marked', async () => {
  // Example: #history-open -> 2 entries; #history-previous -> version 1 read, its entry aria-selected; previous then not offered, next offered.
  // Given g opened (current version 2)
  const { root, reads, viewer } = page();
  await viewer.start();
  const before = root.querySelector('#history-open').getAttribute('disabled');
  await viewer.open('g');
  // When the history is opened and previous pressed by their buttons
  root.querySelector('#history-open').click();
  await flush();
  root.querySelector('#history-previous').click();
  await flush();
  // Then version 1 was read and is marked, and only next is offered
  assert.equal(before, '');
  assert.deepEqual(reads, [null, 1]);
  assert.equal(root.querySelector('[data-version="1"]').getAttribute('aria-selected'), 'true');
  assert.deepEqual(['#history-previous', '#history-next'].map((s) => root.querySelector(s).getAttribute('disabled')), ['', null]);
});
