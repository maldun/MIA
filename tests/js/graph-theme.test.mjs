// The graph page follows the main app's theme choice (graph_app/theme.js, REQ-GA-016 as changed by A-176, D-503).
// Run: node --test tests/js/graph-theme.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { chosenTheme, followTheme, THEME_CHANGED } from '../../graph_app/theme.js';
import { visDrawing } from '../../graph_app/drawing.js';

function storage(values = {}) {
  return { getItem: (k) => (k in values ? values[k] : null), values };
}

/** a window with listeners the test can fire, and a storage */
function fakeWindow(values) {
  const listeners = {};
  return {
    localStorage: storage(values),
    addEventListener: (type, fn) => { (listeners[type] ??= []).push(fn); },
    dispatchEvent: (event) => { for (const fn of listeners[event.type] ?? []) fn(event); return true; },
    fire: (type, event = {}) => { for (const fn of listeners[type] ?? []) fn({ type, ...event }); },
    listeners,
  };
}

test('A-176: the saved choice dark, light or auto is the theme; nothing, an unknown value or a blocked storage is auto', () => {
  // Example: mia.theme = dark -> dark; purple -> auto
  assert.equal(chosenTheme(storage({ 'mia.theme': 'dark' })), 'dark');
  assert.equal(chosenTheme(storage({ 'mia.theme': 'light' })), 'light');
  assert.equal(chosenTheme(storage({ 'mia.theme': 'auto' })), 'auto');
  assert.equal(chosenTheme(storage({ 'mia.theme': 'purple' })), 'auto');
  assert.equal(chosenTheme(storage()), 'auto');
  assert.equal(chosenTheme(null), 'auto');
  assert.equal(chosenTheme({ getItem() { throw new Error('blocked'); } }), 'auto');
});

test('A-176: the page takes the saved choice at once and again when another page of the origin saves a new one', () => {
  // Given the main app's choice dark
  const win = fakeWindow({ 'mia.theme': 'dark' });
  const root = { dataset: { theme: 'auto' } };
  const changed = [];
  win.addEventListener(THEME_CHANGED, () => changed.push(root.dataset.theme));
  // When the page starts
  followTheme(win, root);
  // Then it shows dark
  assert.equal(root.dataset.theme, 'dark');
  // When the main app in another tab saves light
  win.localStorage.values['mia.theme'] = 'light';
  win.fire('storage', { key: 'mia.theme' });
  // Then the page shows light and says so, after the theme was set
  assert.equal(root.dataset.theme, 'light');
  assert.deepEqual(changed, ['light']);
  // And another key changes nothing
  win.fire('storage', { key: 'graphViewer.settings' });
  assert.deepEqual(changed, ['light']);
});

test('A-176, V-2: a theme change re-colours the shown picture', () => {
  // Given a drawn graph and the tokens' colour
  const scheme = { colour: 'rgb(230, 230, 230)' };
  globalThis.getComputedStyle = () => ({ getPropertyValue: (prop) => (prop === 'color' ? scheme.colour : 'sans-serif') });
  const doc = { body: { append() {} }, createElement: () => ({ style: { setProperty() {} }, remove() {} }) };
  const win = { ...fakeWindow({}), matchMedia: () => ({ addEventListener() {} }), setTimeout: (fn) => fn() };
  const nodes = {};
  class DataSet { constructor(items = []) { for (const i of items) nodes[i.id] = i; } update(c) { for (const i of [c].flat()) Object.assign(nodes[i.id], i); } }
  class Network { on() {} setOptions() {} setData() {} }
  const drawing = visDrawing({ ownerDocument: doc }, { DataSet, Network }, win);
  drawing.show({ nodes: [{ id: 'a', label: 'a', shape: 'box', marks: [] }], edges: [] }, { physics: false, layout: 'free', edges: 'rounded' });
  // When the theme changes
  scheme.colour = 'rgb(20, 20, 20)';
  win.fire(THEME_CHANGED);
  // Then the label takes the new colour
  assert.equal(nodes.a.font.color, 'rgb(20, 20, 20)');
});
