// The node-and-edge view of the Graph app (N-5 T-01): REQ-GA-001 (TC-GA-001 is the owner's demonstration). node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { graphOf, layout, svgMarkup } from '../../graph_app/graph-view.js';

const LOOKUP = {
  nodes: [{ id: 'question', kind: 'data' }, { id: 'search', kind: 'process' }, { id: 'hits', kind: 'data' },
    { id: 'judge', kind: 'process' }, { id: 'verdict', kind: 'data' }],
  edges: [{ from: 'question', to: 'search' }, { from: 'search', to: 'hits' }, { from: 'hits', to: 'judge' }, { from: 'judge', to: 'verdict' }],
};
 const count = (text, part) => text.split(part).length - 1;

test('REQ-GA-001: every node and every edge of the lookup is drawn', () => {
  const svg = svgMarkup(LOOKUP);
  assert.equal(count(svg, '<g class="node '), 5);
  assert.equal(count(svg, '<line class="edge"'), 4);
  for (const node of LOOKUP.nodes) assert.ok(svg.includes(`data-id="${node.id}"`), node.id);
  for (const edge of LOOKUP.edges) assert.ok(svg.includes(`data-from="${edge.from}" data-to="${edge.to}"`), `${edge.from}->${edge.to}`);
});

test('REQ-GA-001: data nodes and process nodes are drawn differently', () => {
  const svg = svgMarkup(LOOKUP);
  assert.equal(count(svg, '<g class="node data"'), 3);
  assert.equal(count(svg, '<g class="node process"'), 2);
});

test('REQ-GA-001: every edge points to a later layer', () => {
  const placed = layout(LOOKUP);
  const layer = Object.fromEntries(placed.nodes.map((n) => [n.id, n.layer]));
  assert.deepEqual(placed.nodes.map((n) => n.layer), [0, 1, 2, 3, 4]);
  for (const edge of placed.edges) assert.ok(layer[edge.to] > layer[edge.from], `${edge.from}->${edge.to}`);
});

test('REQ-GA-001: nodes of the same layer get different rows and no two nodes share a place', () => {
  const graph = { nodes: [{ id: 'q', kind: 'data' }, { id: 'a', kind: 'process' }, { id: 'b', kind: 'process' }],
    edges: [{ from: 'q', to: 'a' }, { from: 'q', to: 'b' }] };
  const placed = layout(graph);
  assert.deepEqual(placed.nodes.map((n) => [n.id, n.layer, n.row]), [['q', 0, 0], ['a', 1, 0], ['b', 1, 1]]);
  assert.equal(new Set(placed.nodes.map((n) => `${n.x},${n.y}`)).size, 3);
  for (const n of placed.nodes) { assert.ok(n.x > 0 && n.x < placed.width, n.id); assert.ok(n.y > 0 && n.y < placed.height, n.id); }
});

test('REQ-GA-001: a library entry is drawn from its workflow', () => {
  assert.equal(graphOf({ workflow: LOOKUP, enabled: true }), LOOKUP);
  assert.equal(graphOf(LOOKUP), LOOKUP);
  assert.throws(() => graphOf({ title: 'no graph' }), /no graph/);
});

test('REQ-GA-001: a cycle and an edge to an unknown id still give a drawing', () => {
  const graph = { nodes: [{ id: 'a', kind: 'data' }, { id: 'b', kind: 'process' }],
    edges: [{ from: 'a', to: 'b' }, { from: 'b', to: 'a' }, { from: 'b', to: 'ghost' }] };
  const placed = layout(graph);
  assert.equal(placed.nodes.length, 2);
  assert.equal(placed.edges.length, 2);
  assert.equal(count(svgMarkup(graph), '<line class="edge"'), 2);
});

test('REQ-GA-001: ids are escaped in the drawing', () => {
  const svg = svgMarkup({ nodes: [{ id: '<b>&', kind: 'data' }], edges: [] });
  assert.ok(svg.includes('&lt;b&gt;&amp;'));
  assert.ok(!svg.includes('<b>&'));
});
