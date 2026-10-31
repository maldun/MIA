// The node-and-edge view of the Graph app (N-5 T-01, reworked for vis-network by D-124): REQ-GA-001 (TC-GA-001 is the owner's demonstration).
// Only the pure part is tested here (graph document -> vis nodes, edges and options); the drawing in the browser is checked by hand. node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { graphsOf, layout, visData, visOptions } from '../../graph_app/graph-view.js';

const LOOKUP = {
  nodes: [{ id: 'question', kind: 'data' }, { id: 'search', kind: 'process' }, { id: 'hits', kind: 'data' },
    { id: 'judge', kind: 'process' }, { id: 'verdict', kind: 'data' }],
  edges: [{ from: 'question', to: 'search' }, { from: 'search', to: 'hits' }, { from: 'hits', to: 'judge' }, { from: 'judge', to: 'verdict' }],
};
const CONTEXT = { nodes: [{ id: 'question', kind: 'data' }], edges: [] };
const COLORS = { data: '#dbeafe', process: '#fde68a', line: '#6b7280', text: '#1d1d1f' };

test('REQ-GA-001: every node and every edge of the lookup becomes a vis node or a directed vis edge', () => {
  // Given: LOOKUP
  // When:
  const { nodes, edges, problems } = visData(LOOKUP);
  // Then:
  assert.deepEqual(nodes.map((n) => n.id), ['question', 'search', 'hits', 'judge', 'verdict']);
  assert.deepEqual(nodes.map((n) => n.label), ['question', 'search', 'hits', 'judge', 'verdict']);
  assert.deepEqual(edges.map((e) => [e.from, e.to]), [['question', 'search'], ['search', 'hits'], ['hits', 'judge'], ['judge', 'verdict']]);
  assert.deepEqual(edges.map((e) => e.id), ['e0', 'e1', 'e2', 'e3']);
  assert.ok(edges.every((e) => e.arrows === 'to'));
  assert.deepEqual(problems, []);
});

test('REQ-GA-001: data nodes and process nodes are in different groups, and the groups look different', () => {
  // Given: LOOKUP and COLORS
  // When:
  const { nodes } = visData(LOOKUP);
  const options = visOptions(COLORS);
  // Then:
  assert.deepEqual(nodes.map((n) => n.group), ['data', 'process', 'data', 'process', 'data']);
  assert.equal(options.groups.data.shape, 'ellipse');
  assert.equal(options.groups.process.shape, 'box');
  assert.equal(options.groups.data.color, COLORS.data);
  assert.equal(options.groups.process.color, COLORS.process);
});

test('REQ-GA-001: the layout is stable: every edge points to a later layer and the same graph gives the same places', () => {
  // Given: LOOKUP
  // When:
  const placed = layout(LOOKUP);
  const layer = Object.fromEntries(placed.nodes.map((n) => [n.id, n.layer]));
  // Then:
  assert.deepEqual(placed.nodes.map((n) => n.layer), [0, 1, 2, 3, 4]);
  for (const edge of placed.edges) assert.ok(layer[edge.to] > layer[edge.from], `${edge.from}->${edge.to}`);
  assert.deepEqual(visData(LOOKUP).nodes.map((n) => [n.x, n.y]), [[0, 0], [180, 0], [360, 0], [540, 0], [720, 0]]);
  assert.deepEqual(visData(LOOKUP).nodes.map((n) => [n.x, n.y]), visData(LOOKUP).nodes.map((n) => [n.x, n.y]));
});

test('REQ-GA-001: nodes of the same layer get different rows and no two nodes share a place', () => {
  // Given:
  const graph = { nodes: [{ id: 'q', kind: 'data' }, { id: 'a', kind: 'process' }, { id: 'b', kind: 'process' }],
    edges: [{ from: 'q', to: 'a' }, { from: 'q', to: 'b' }] };
  // When:
  const placed = layout(graph);
  // Then:
  assert.deepEqual(placed.nodes.map((n) => [n.id, n.layer, n.row]), [['q', 0, 0], ['a', 1, 0], ['b', 1, 1]]);
  assert.equal(new Set(placed.nodes.map((n) => `${n.x},${n.y}`)).size, 3);
});

test('REQ-GA-001: the user can drag nodes, they stay where they are dropped, and edges are arrows', () => {
  // Given: COLORS
  // When:
  const options = visOptions(COLORS);
  // Then:
  assert.equal(options.physics, false);
  assert.equal(options.layout.hierarchical, false);
  assert.equal(options.interaction.dragNodes, true);
  assert.equal(options.edges.arrows.to.enabled, true);
});

test('REQ-GA-001: a plain graph, a library entry, a record read through IF-104 and a stored version list are opened', () => {
  // Given: LOOKUP and CONTEXT
  // When / Then:
  assert.deepEqual(graphsOf(LOOKUP), [{ name: 'graph', graph: LOOKUP }]);
  assert.deepEqual(graphsOf({ workflow: LOOKUP, context_graph: CONTEXT, enabled: true }), [{ name: 'workflow', graph: LOOKUP }, { name: 'context graph', graph: CONTEXT }]);
  assert.deepEqual(graphsOf({ workflow: LOOKUP, enabled: true }), [{ name: 'workflow', graph: LOOKUP }]);
  assert.deepEqual(graphsOf({ id: 'lookup', version: 2, author: 'anna', time: 't', doc: LOOKUP }), [{ name: 'lookup version 2', graph: LOOKUP }]);
  assert.deepEqual(graphsOf([{ id: 'lookup', version: 1, doc: CONTEXT }, { id: 'lookup', version: 2, doc: LOOKUP }]), [{ name: 'lookup version 2', graph: LOOKUP }]);
  assert.throws(() => graphsOf({ title: 'no graph' }), /no graph/);
  assert.throws(() => graphsOf([]), /no graph/);
});

test('REQ-GA-001: a cycle, an edge to an unknown id and a repeated id still give a drawing, with the problems named', () => {
  // Given:
  const graph = { nodes: [{ id: 'a', kind: 'data' }, { id: 'b', kind: 'process' }, { id: 'a', kind: 'process' }],
    edges: [{ from: 'a', to: 'b' }, { from: 'b', to: 'a' }, { from: 'b', to: 'ghost' }] };
  // When:
  const { nodes, edges, problems } = visData(graph);
  // Then:
  assert.deepEqual(nodes.map((n) => n.id), ['a', 'b']);
  assert.deepEqual(edges.map((e) => [e.id, e.from, e.to]), [['e0', 'a', 'b'], ['e1', 'b', 'a']]);
  assert.deepEqual(problems, ['node a: the id is used twice', 'edge b->ghost: unknown node']);
});

test('REQ-GA-001: a label is the id as plain text, never markup', () => {
  // Given:
  const graph = { nodes: [{ id: '<b>&', kind: 'data' }], edges: [] };
  // When:
  const { nodes } = visData(graph);
  // Then:
  assert.equal(nodes[0].label, '<b>&');
  assert.equal(visOptions(COLORS).nodes.font.multi, false);
});
