// The arrangement of a graph (graph_app/arrangement.js, R6, REQ-GA-030, REQ-GA-032, REQ-GA-033). Run: node --test tests/js/graph-arrangement.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { placed, layered } from '../../graph_app/arrangement.js';

const nodes = (...ids) => ids.map((id) => ({ id, label: id }));
const edge = (id, from, to) => ({ id, from, to, arrows: 'to' });

test('REQ-GA-030: saved places are used and held; steps without one are left to the solver', () => {
  // Example: a at 10, -3 saved, b moved to 5, 6 -> a {x: 10, y: -3, fixed}, b {x: 5, y: 6, fixed}, c no place; a place of an unknown step ignored.
  // Given three steps, a saved place for a and z, and b moved by the owner
  // When the places are applied
  const out = placed(nodes('a', 'b', 'c'), { a: { x: 10, y: -3 }, z: { x: 1, y: 1 } }, { b: { x: 5, y: 6 } });
  // Then a and b are placed and held, c is free, and z is not drawn
  assert.deepEqual(out.map((n) => [n.id, n.x, n.y, n.fixed]), [['a', 10, -3, true], ['b', 5, 6, true], ['c', undefined, undefined, undefined]]);
});

test('REQ-GA-032: a moved place wins over the saved one', () => {
  // Example: a saved at 10, -3 and moved to 50, 50 -> 50, 50.
  // Given a saved and a moved place for a
  // When applied
  // Then the moved place is used
  assert.deepEqual(placed(nodes('a'), { a: { x: 10, y: -3 } }, { a: { x: 50, y: 50 } }).map((n) => [n.x, n.y]), [[50, 50]]);
});

test('REQ-GA-033: the layers point every connection forward, also with branches and joins', () => {
  // Example: a -> b -> d, a -> c -> d, a -> d -> levels a 0, b 1, c 1, d 2; every edge from lower to higher.
  // Given a graph with a branch and a join
  const ns = nodes('a', 'b', 'c', 'd');
  const es = [edge('e1', 'a', 'b'), edge('e2', 'a', 'c'), edge('e3', 'b', 'd'), edge('e4', 'c', 'd'), edge('e5', 'a', 'd')];
  // When the layers are made
  const level = Object.fromEntries(layered(ns, es).map((n) => [n.id, n.level]));
  // Then each connection goes forward
  assert.deepEqual(level, { a: 0, b: 1, c: 1, d: 2 });
  for (const e of es) assert.ok(level[e.from] < level[e.to], e.id);
});

test('REQ-GA-033: a cycle still gives every step a whole-number layer, and no place is held', () => {
  // Example: a -> b -> a, b -> c -> levels for a, b, c, all integers; a placed node loses x, y and fixed.
  // Given a cycle (a graph the rules refuse, but a stored one can hold) and a placed step
  const ns = [{ id: 'a', x: 1, y: 2, fixed: true }, { id: 'b' }, { id: 'c' }];
  // When the layers are made
  const out = layered(ns, [edge('e1', 'a', 'b'), edge('e2', 'b', 'a'), edge('e3', 'b', 'c')]);
  // Then every step has a layer and nothing is held at a place
  assert.ok(out.every((n) => Number.isInteger(n.level)));
  assert.ok(out.every((n) => n.x === undefined && n.y === undefined && !n.fixed));
  const level = Object.fromEntries(out.map((n) => [n.id, n.level]));
  assert.ok(level.b < level.c);
});
