// The frame of the graph viewer (graph_app/viewer.js, REQ-GA-012, REQ-GA-013) on the fake DOM; the browser checks (TC-GA-033) see it in Firefox.
// Run: node --test tests/js/graph-viewer-frame.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument } from './fake-dom.mjs';
import { createViewer } from '../../graph_app/viewer.js';

const AREAS = ['graph-list', 'search-band', 'other-things', 'left-column', 'picture', 'actions-row', 'history-row', 'status-bar'];
const CONTROLS = 'button,input,select,textarea,a';

function page(api = {}) {
  const doc = installDocument();
  const root = doc.createElement('div');
  doc.body.append(root);
  return { root, viewer: createViewer({ document: doc, root, api }) };
}

test('REQ-GA-012: every area of the owner\'s layout is there once, with a label and a heading', () => {
  // Example: [data-area=picture] once, aria-label "Picture", its h2 "Picture".
  // Given a new viewer
  const { root } = page();
  // When the areas are looked up
  // Then each is there once, labelled, with the label as its heading
  for (const name of AREAS) {
    const found = root.querySelectorAll(`[data-area=${name}]`);
    assert.equal(found.length, 1, name);
    const label = found[0].getAttribute('aria-label');
    assert.ok(label, name);
    assert.equal(found[0].querySelector('h2').textContent, label);
  }
});

test('REQ-GA-013: the areas of later subgoals hold one line naming the subgoal and no control', () => {
  // Example: [data-later=EDIT] inside the actions row names G-V4.EDIT; [data-later=SEARCH] inside the search band names the search.
  // Given a new viewer
  const { root } = page();
  // When the later areas are read
  const where = { SEARCH: 'search-band', EDIT: 'actions-row', REPLAY: 'history-row', RUN: 'history-row' };
  // Then each sits in its area, is one line naming the subgoal, and holds no control
  for (const [name, inside] of Object.entries(where)) {
    const el = root.querySelector(`[data-area=${inside}] [data-later=${name}]`);
    assert.ok(el, name);
    assert.ok(!el.textContent.includes('\n'));
    assert.ok(el.textContent.toLowerCase().includes(name.toLowerCase()), el.textContent);
    assert.equal(el.querySelectorAll(CONTROLS).length, 0);
  }
});

test('REQ-GA-018: start fills the store entry from the store route', async () => {
  // Example: database, not reachable -> the entry reads "store: database, not reachable".
  // Given a store route answering database, not reachable
  const api = { me: async () => ({ user: 'anna', owner: true }), store: async () => ({ store: 'database', reachable: false, shown: 'live' }), listGraphs: async () => [] };
  const { root, viewer } = page(api);
  // When the page starts
  await viewer.start();
  // Then other things names the store and that it does not answer
  assert.equal(root.querySelector('[data-area=other-things] [data-store]').textContent, 'store: database, not reachable');
});
