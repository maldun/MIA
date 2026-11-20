// PROTOTYPE CP7 checks (node --test): the arrangement (FR-52), the history list and stepping (FR-55), and a first look at layout time (NFR-11)
import test from 'node:test';
import assert from 'node:assert/strict';
import { applyPositions, positionsOf, arrangementNote } from '../graph_app_v2/arrangement.js';
import { historyEntries, neighbour, versionNote } from '../graph_app_v2/history.js';
import { visData } from '../graph_app/graph-view.js';

const nodes = [{ id: 'a', x: 0, y: 0 }, { id: 'b', x: 180, y: 0 }, { id: 'c', x: 360, y: 0 }];

test('FR-52: a saved arrangement puts the steps where the owner left them; with every step placed no physics is needed', () => {
  const all = applyPositions(nodes, { a: { x: 5, y: 6 }, b: { x: 7, y: 8 }, c: { x: 9, y: 10 } });
  assert.deepEqual(all.nodes.map((n) => [n.x, n.y]), [[5, 6], [7, 8], [9, 10]]);
  assert.equal(all.fixed, true);
});

test('FR-52: a step without a saved place keeps its layered place and the rest settles; no saved arrangement changes nothing', () => {
  const some = applyPositions(nodes, { a: { x: 5, y: 6 } });
  assert.deepEqual(some.nodes.map((n) => [n.x, n.y]), [[5, 6], [180, 0], [360, 0]]);
  assert.equal(some.fixed, false);
  assert.deepEqual(applyPositions(nodes, null), { nodes, fixed: false });
  assert.deepEqual(applyPositions(nodes, {}), { nodes, fixed: false });
});

test('FR-52: the places to save are whole numbers; the owner is told which arrangement is in use', () => {
  assert.deepEqual(positionsOf({ a: { x: 1.4, y: 2.6 } }), { a: { x: 1, y: 3 } });
  assert.deepEqual(positionsOf(null), {});
  assert.match(arrangementNote({ positions: { a: {} }, version: 2, author: 'owner' }, 'auto'), /Saved arrangement \(version 2, owner\)/);
  assert.match(arrangementNote({ positions: null }, 'auto'), /settles by itself/);
  assert.match(arrangementNote({ positions: { a: {} }, version: 1, author: 'o' }, 'layers'), /Layered arrangement .*unchanged/);
});

const versions = [{ version: 1, author: 'owner', time: '2026-11-20T10:00:00Z' }, { version: 3, author: 'author3', time: '2026-11-20T12:00:00Z' }, { version: 2, author: 'author2', time: '2026-11-20T11:00:00Z' }];

test('FR-55: the history lists the versions newest first with who and when, and marks the current one', () => {
  const e = historyEntries(versions, 3);
  assert.deepEqual(e.map((x) => x.version), [3, 2, 1]);
  assert.match(e[0].text, /version 3 \(current\)  author3  2026-11-20 12:00:00/);
  assert.equal(e.filter((x) => x.current).length, 1);
});

test('FR-55: stepping goes to the previous and the next version and stops at the ends', () => {
  assert.equal(neighbour(versions, 2, 'previous'), 1);
  assert.equal(neighbour(versions, 2, 'next'), 3);
  assert.equal(neighbour(versions, 1, 'previous'), null);
  assert.equal(neighbour(versions, 3, 'next'), null);
  assert.equal(neighbour(versions, 9, 'next'), null);
});

test('FR-55: the page says which version is shown and that an earlier one is read-only', () => {
  assert.equal(versionNote(3, 3), 'version 3 (the current one)');
  assert.match(versionNote(1, 3), /version 1 of 3: an earlier version, read-only/);
});

test('NFR-11: the layout of a graph of about fifty steps takes a few milliseconds (first look, node)', () => {
  const n = 54, g = { nodes: [], edges: [] };
  for (let i = 0; i < n; i += 1) g.nodes.push({ id: `s${i}`, kind: i % 2 ? 'process' : 'data' });
  for (let i = 1; i < n; i += 1) { g.edges.push({ id: `e${i}`, from: `s${i - 1}`, to: `s${i}` }); if (i > 3) g.edges.push({ id: `x${i}`, from: `s${i - 3}`, to: `s${i}` }); }
  const times = [];
  for (let k = 0; k < 20; k += 1) { const t0 = performance.now(); visData(g); times.push(performance.now() - t0); }
  times.sort((a, b) => a - b);
  console.log(`layout of ${n} steps and ${g.edges.length} connections: median ${times[10].toFixed(2)} ms`);
  assert.ok(times[10] < 50);
});
