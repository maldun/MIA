// Stand-ins of the node checks of the graph viewer page (G-V4.VIEW, protected; page-interface-note.md section 4, TR-VIEW-004, 005).
// The page runs on the fake DOM of tests/js/fake-dom.mjs (D-443), reads IF-104 v2 through its own api.js over the JS mock's fetch (TR-VIEW-004:
// only through the routes), and hands its pictures to a recording drawing (TR-VIEW-005: the checks read what the page hands to the library).
import { readFileSync } from 'node:fs';
import { installDocument, flush } from '../js/fake-dom.mjs';
import { GraphApiV2Mock } from './mocks/if_104_v2_graph_api.mjs';

export { flush };
export const HOSTILE = '<img src=x onerror=alert(1)> step "quoted" & more';
const FIXTURE = new URL('../fixtures/graph_view/graphs.json', import.meta.url);

/** every fixture version in stored order (TR-VIEW-002) */
export function fixtureVersions() { return JSON.parse(readFileSync(FIXTURE, 'utf8')).versions; }

/** the JS mock holding the fixture versions (all, or those of `ids`), anna (the owner) logged in unless `login` is false */
export async function seededMock(ids = null, { login = true } = {}) {
  const mock = new GraphApiV2Mock();
  for (const v of fixtureVersions()) if (ids === null || ids.includes(v.graph.id)) mock.seed(structuredClone(v.graph), v.author);
  if (login) {
    const answer = await mock.fetch('/api/login', { method: 'POST', body: JSON.stringify({ user: 'anna', password: 'pw-anna' }), headers: { Origin: mock.origin } });
    if (answer.status !== 200) throw new Error('login to the mock failed');
  }
  return mock;
}

/** the answer of one GET to the mock, for expected values taken from the contract side (times) */
export async function mockGet(mock, path) { return (await mock.fetch(path)).json(); }

/** a drawing that records what the page hands to it (page-interface-note.md section 3); a `show` places every node at its given x, y or on a row */
export function recordingDrawing() {
  const rec = { shows: [], options: [], optionsAtLastShow: 0, places: {}, dragEnd: null, stabilized: null, containers: [] };
  rec.make = (container) => {
    rec.containers.push(container);
    return {
      show(data, options) {
        rec.shows.push({ data: structuredClone(data), options: structuredClone(options ?? {}) });
        rec.optionsAtLastShow = rec.options.length;
        rec.places = {};
        data.nodes.forEach((n, i) => { rec.places[n.id] = { x: n.x ?? i * 100, y: n.y ?? 0 }; });
      },
      setOptions(options) { rec.options.push(structuredClone(options)); },
      positions() { return structuredClone(rec.places); },
      onDragEnd(fn) { rec.dragEnd = fn; },
      onStabilized(fn) { rec.stabilized = fn; },
    };
  };
  rec.last = () => rec.shows.at(-1);
  /** the owner drags a step: its place changes in the drawing and the page hears the drag end */
  rec.drag = (id, x, y) => { rec.places[id] = { x, y }; rec.dragEnd?.({ id, x, y }); };
  /** the options in force: those of the last show, then every setOptions after it */
  rec.current = () => {
    let merged = rec.shows.length ? { ...rec.last().options } : {};
    for (const o of rec.options.slice(rec.optionsAtLastShow)) merged = { ...merged, ...o };
    return merged;
  };
  return rec;
}

/** a localStorage-like store in memory */
export function memoryStorage() {
  const data = new Map();
  return { getItem: (k) => (data.has(k) ? data.get(k) : null), setItem: (k, v) => { data.set(k, String(v)); }, removeItem: (k) => { data.delete(k); } };
}

/** a storage whose every read and write throws, as a blocked localStorage (REQ-GA-035) */
export function throwingStorage() {
  const no = () => { throw new Error('storage blocked'); };
  return { getItem: no, setItem: no, removeItem: no };
}

/** a fresh fake document with a root, the viewer created on it over the mock (page-interface-note.md section 1) */
export async function pageWith({ mock, storage = memoryStorage() }) {
  const doc = installDocument();
  const root = doc.createElement('div');
  root.setAttribute('id', 'app');
  doc.body.append(root);
  const drawing = recordingDrawing();
  const { createViewer } = await import('../../graph_app/viewer.js');
  const { httpApi } = await import('../../graph_app/api.js');
  const viewer = createViewer({ document: doc, root, api: httpApi(mock.fetch), storage, makeDrawing: drawing.make });
  return { doc, root, viewer, drawing, mock };
}

/** the list entries the owner can see (not hidden) */
export function listed(root) {
  return root.querySelectorAll('[data-graph-id]').filter((el) => el.getAttribute('hidden') === null && el.hidden !== true).map((el) => el.dataset.graphId);
}

/** the text of the first element matching `selector`, '' when there is none */
export function textOf(root, selector) { return root.querySelector(selector)?.textContent ?? ''; }

/** the value part of a left-column field, `<label>: <value>` -> value */
export function fieldValue(root, name) {
  const text = textOf(root, `[data-field="${name}"]`);
  return text.includes(':') ? text.slice(text.indexOf(':') + 1).trim() : null;
}

/** a button the page offers: present and not disabled */
export function offered(root, selector) {
  const el = root.querySelector(selector);
  return Boolean(el) && el.getAttribute('disabled') === null && el.disabled !== true;
}

/** GET requests the mock received for `path` */
export function gets(mock, path) { return mock.requests.filter((r) => r.method === 'GET' && r.path === path).length; }
