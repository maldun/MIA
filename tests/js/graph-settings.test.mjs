// The view settings of the graph viewer (graph_app/settings.js, R6, REQ-GA-034, REQ-GA-035). Run: node --test tests/js/graph-settings.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { KEY, DEFAULTS, loadSettings, saveSettings, drawingOptions } from '../../graph_app/settings.js';

const memory = (init = {}) => { const m = new Map(Object.entries(init)); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), m }; };
const blocked = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };

test('REQ-GA-035: saved settings come back; none, damaged or blocked give the defaults', () => {
  // Example: {"edges":"straight","arrangement":"off"} -> the same; nothing, "{", {"edges":"wavy"} and a throwing storage -> rounded and on.
  // Given storages holding good, missing, damaged and odd settings, and a blocked one
  const good = memory({ [KEY]: JSON.stringify({ edges: 'straight', arrangement: 'off' }) });
  const odd = memory({ [KEY]: JSON.stringify({ edges: 'wavy', arrangement: 1 }) });
  // When the settings are loaded
  // Then the good ones come back and every other case gives the defaults
  assert.deepEqual(loadSettings(good), { edges: 'straight', arrangement: 'off' });
  for (const s of [memory(), memory({ [KEY]: '{' }), odd, blocked, null]) assert.deepEqual(loadSettings(s), DEFAULTS);
  assert.deepEqual(DEFAULTS, { edges: 'rounded', arrangement: 'on' });
});

test('REQ-GA-035: saving says whether the settings were kept', () => {
  // Example: a memory storage -> true and the JSON under KEY; a blocked storage -> false, no throw.
  // Given a working and a blocked storage
  const store = memory();
  // When the settings are saved into each
  // Then the working one keeps them, the blocked one reports false
  assert.equal(saveSettings(store, { edges: 'straight', arrangement: 'off' }), true);
  assert.deepEqual(JSON.parse(store.m.get(KEY)), { edges: 'straight', arrangement: 'off' });
  assert.equal(saveSettings(blocked, DEFAULTS), false);
});

test('REQ-GA-031, REQ-GA-034: the drawing options carry the settings and the fixed seed and solver', () => {
  // Example: straight + off -> {edges: straight, physics: false, seed, solver, layout: settle}; the seed and solver never change.
  // Given two settings
  const a = drawingOptions({ edges: 'straight', arrangement: 'off' });
  const b = drawingOptions(DEFAULTS, 'layered');
  // When their options are compared
  // Then the settings show, and seed and solver are the same constants
  assert.deepEqual([a.edges, a.physics, a.layout], ['straight', false, 'settle']);
  assert.deepEqual([b.edges, b.physics, b.layout], ['rounded', true, 'layered']);
  assert.deepEqual([a.seed, a.solver], [b.seed, b.solver]);
  assert.ok(Number.isInteger(a.seed) && typeof a.solver === 'string');
});
