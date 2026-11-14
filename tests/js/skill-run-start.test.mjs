// The start of the Skill run view (F-13 of the second Verify run of G-V3.PANEL, REQ-CLV-037, 038): a reload with a link to a run that cannot be opened shows the run the backend names.
// node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, fakeSocket, flush } from './fake-dom.mjs';

const SHOWN = { id: 'r7', skill: 'review', version: '1', started: '2026-11-08T10:00:00Z', state: 'done', phases: [], answers: [], material: [], files: [], elements: [] };

/** the view on a fake page: the elements of the strip are made on first use, `hash` is the address of the page, the api answers as the tests say */
async function startView(hash, api) {
  const doc = installDocument();
  doc.documentElement = { style: { setProperty() {} } };
  doc.addEventListener = () => {};
  globalThis.location = { hash };
  globalThis.ResizeObserver = class { observe() {} };
  const nodes = new Map();
  const root = { offsetHeight: 0, scrollIntoView() {}, querySelector(selector) {
    if (!nodes.has(selector)) {
      const node = doc.createElement('div');
      node.scrollIntoView = () => {};
      nodes.set(selector, node);
    }
    return nodes.get(selector);
  } };
  const { initSkillRunView } = await import('../../templates/static/chat/skill-run.js');
  const socket = fakeSocket();
  const notes = [];
  const view = initSkillRunView({ root, socket, api: { files: async () => [], ...api }, t: (key) => key, notify: (text) => notes.push(text) });
  socket.fire('connect');
  await flush();
  return { view, notes };
}

test('TC-CLV-038: a reload with a link to a run that cannot be opened shows the run the backend names', async () => {
  // Given: a page address that names the run "gone" (deleted, or of another account: the backend answers not found) and a backend whose shown run is r7
  const api = { skillRun: async () => { throw new Error('404'); }, shownRun: async () => SHOWN };
  // When: the page starts
  const { view } = await startView('#run=gone', api);
  // Then: the view shows r7, the run the backend names
  assert.equal(view.shown()?.id, 'r7');
});

test('TC-CLV-037: a reload with a link to a run that opens shows that run, not the one the backend names', async () => {
  // Given: a page address that names r2, a backend that has r2, and a shown run r7
  const api = { skillRun: async (id) => ({ ...SHOWN, id }), shownRun: async () => SHOWN };
  // When: the page starts
  const { view } = await startView('#run=r2', api);
  // Then: the view shows r2
  assert.equal(view.shown()?.id, 'r2');
});
