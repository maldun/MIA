// The list and the opening of the graph viewer (graph_app/viewer.js, REQ-GA-019 to 023) beyond the acceptance checks: keys, clicks, notices.
// Run: node --test tests/js/graph-viewer-list.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, flush } from './fake-dom.mjs';
import { createViewer } from '../../graph_app/viewer.js';

const LIST = [{ id: 'a', kind: 'workflow', version: 1, steps: 1, connections: 0, description: 'first' },
  { id: 'b', kind: 'workflow', version: 2, steps: 2, connections: 1, description: 'second' }];
const GRAPH = (id, version) => ({ graph: { id, nodes: [{ id: 's', data: { type: 'data' } }], edges: [] }, version, current: version, author: 'anna', time: 't', problems: [], steps: {} });

function page(overrides = {}) {
  const doc = installDocument();
  const root = doc.createElement('div');
  doc.body.append(root);
  const calls = [];
  const api = { me: async () => ({ user: 'anna', owner: true }), store: async () => ({ store: 'files', reachable: true, shown: 'live' }),
    listGraphs: async () => LIST, readGraph: async (id) => { calls.push(id); return GRAPH(id, id === 'a' ? 1 : 2); },
    readArrangement: async () => ({ positions: null }), ...overrides };
  const shows = [];
  const makeDrawing = () => ({ show: (data) => shows.push(data), setOptions() {}, positions: () => ({}), onDragEnd() {}, onStabilized() {} });
  return { doc, root, calls, shows, viewer: createViewer({ document: doc, root, api, storage: null, makeDrawing }) };
}
const refused = (status, code) => async () => { throw { status, code, detail: {} }; };

test('REQ-GA-021: a click or Enter on an entry opens that graph; the opened entry is marked', async () => {
  // Example: click on b -> b read and drawn, b aria-current; Enter on a -> a read.
  // Given the started page
  const { root, calls, shows, viewer } = page();
  await viewer.start();
  // When b is clicked and Enter is pressed on a
  root.querySelector('[data-graph-id="b"]').click();
  await flush();
  root.querySelector('[data-graph-id="a"]').dispatchEvent({ type: 'keydown', key: 'Enter' });
  await flush();
  // Then both were read and drawn in that order, and a is the current entry
  assert.deepEqual(calls, ['b', 'a']);
  assert.equal(shows.length, 2);
  assert.equal(root.querySelector('[data-graph-id="a"]').getAttribute('aria-current'), 'true');
  assert.equal(root.querySelector('[data-graph-id="b"]').getAttribute('aria-current'), null);
});

test('REQ-GA-019: the entries are tab stops and the arrow keys move between the shown ones', async () => {
  // Example: ArrowDown on a -> b gets the focus; ArrowUp on b -> a; with "second" filtered, ArrowDown on b stays.
  // Given the started page
  const { doc, root, viewer } = page();
  await viewer.start();
  const [a, b] = ['a', 'b'].map((id) => root.querySelector(`[data-graph-id="${id}"]`));
  // When the arrow keys are pressed
  a.dispatchEvent({ type: 'keydown', key: 'ArrowDown' });
  const afterDown = doc.activeElement;
  b.dispatchEvent({ type: 'keydown', key: 'ArrowUp' });
  const afterUp = doc.activeElement;
  // Then the focus moves along the list, and every entry is a tab stop
  assert.equal(afterDown, b);
  assert.equal(afterUp, a);
  assert.deepEqual([a, b].map((e) => e.getAttribute('tabindex')), ['0', '0']);
});

test('REQ-GA-022: a session that ends after opening empties the list and the picture and offers the login', async () => {
  // Example: a opened, then 401 on the next opening -> no entry, the picture hidden, [data-login] with a link to /.
  // Given a opened
  const state = { gone: false };
  const { root, viewer } = page({ readGraph: async (id) => { if (state.gone) throw { status: 401, code: 'unauthenticated', detail: {} }; return GRAPH(id, 1); } });
  await viewer.start();
  await viewer.open('a');
  // When the session is gone and b is opened
  state.gone = true;
  await viewer.open('b');
  // Then nothing of the graphs is shown, and the login is offered
  assert.equal(root.querySelectorAll('[data-graph-id]').length, 0);
  assert.equal(root.querySelector('[data-area=picture] [data-drawing]').hidden, true);
  assert.ok(root.querySelector('[data-login] a[href="/"]'));
  assert.ok(!root.querySelector('[data-area=status-bar]').textContent.includes('version'));
});

test('REQ-GA-023: the store notice is one line and goes away once the store answers again', async () => {
  // Example: 503 on the list -> one [data-notice=store_unreachable]; the next start with the store back -> none.
  // Given a list route that fails once with 503
  let down = true;
  const { root, viewer } = page({ listGraphs: async () => { if (down) throw { status: 503, code: 'store_unreachable', detail: {} }; return LIST; } });
  // When the page starts twice, the store answering the second time
  await viewer.start();
  await viewer.start();
  const first = root.querySelectorAll('[data-notice=store_unreachable]').length;
  down = false;
  await viewer.start();
  // Then one notice was shown, then none, and the list is there
  assert.equal(first, 1);
  assert.equal(root.querySelectorAll('[data-notice=store_unreachable]').length, 0);
  assert.equal(root.querySelectorAll('[data-graph-id]').length, 2);
});

test('REQ-GA-022: other failures are not swallowed', async () => {
  // Example: a 500 on the list rejects start.
  // Given a list route answering 500
  const { viewer } = page({ listGraphs: refused(500, null) });
  // When the page starts
  // Then the failure reaches the caller
  await assert.rejects(viewer.start(), (err) => err.status === 500);
});
