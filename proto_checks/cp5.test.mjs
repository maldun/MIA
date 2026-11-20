// PROTOTYPE CP5 checks (node --test): the name filter of the list (FR-48) and the marks for what cannot be drawn (FR-49)
import test from 'node:test';
import assert from 'node:assert/strict';
import { filterGraphs, entryLabel } from '../graph_app_v2/list-filter.js';
import { withProblemMarks } from '../graph_app_v2/problems.js';
import { visData } from '../graph_app/graph-view.js';

const graphs = [
  { id: 'research.escalate@1', kind: 'workflow', version: 1, steps: 54, connections: 65, description: 'research with escalation' },
  { id: 'chat@1', kind: 'workflow', version: 3, steps: 3, connections: 2, description: 'plain chat' },
  { id: 'lookup.context', kind: 'context', version: 2, steps: 5, connections: 4, description: 'knowledge for lookup' },
];

test('FR-48: the list narrows as the owner types part of a name, case ignored, every word must match', () => {
  assert.equal(filterGraphs(graphs, '').length, 3);
  assert.deepEqual(filterGraphs(graphs, 'RES').map((g) => g.id), ['research.escalate@1']);
  assert.deepEqual(filterGraphs(graphs, 'chat').map((g) => g.id), ['chat@1']);
  assert.deepEqual(filterGraphs(graphs, 'context lookup').map((g) => g.id), ['lookup.context']);
  assert.equal(filterGraphs(graphs, 'zzz').length, 0);
});

test('FR-48: every entry says whether it is a workflow graph or a context graph, its version and size', () => {
  assert.match(entryLabel(graphs[2]), /context graph, v2, 5 steps, 4 connections/);
  assert.match(entryLabel(graphs[0]), /workflow graph, v1, 54 steps/);
});

const stored = { id: 'g', nodes: [{ id: 'a', data: { type: 'data' } }, { id: 'b', data: { type: 'transform', toolbox_id: 't' } }],
  edges: [{ id: 'e1', from: 'a', to: 'b', data: {} }, { id: 'e2', from: 'b', to: 'gone', data: {} }] };

test('FR-49: a connection to a missing step is drawn to a marked placeholder, and the problem is named', () => {
  const problems = [{ problem: 'missing_step', connection: 'e2', step: 'gone', end: 'to' }];
  const { graph, named, missing } = withProblemMarks(stored, problems);
  const drawn = visData(graph);
  assert.equal(drawn.problems.length, 0);                           // nothing is dropped by the layout
  assert.equal(drawn.nodes.length, 3);
  assert.equal(drawn.edges.length, 2);
  assert.ok(missing.has('gone'));
  assert.equal(named.length, 1);
  assert.match(named[0], /connection e2: the target step "gone" does not exist/);
});

test('FR-49: a graph without problems is drawn as stored and names nothing', () => {
  const ok = { ...stored, edges: [stored.edges[0]] };
  const { graph, named } = withProblemMarks(ok, []);
  assert.equal(visData(graph).nodes.length, 2);
  assert.deepEqual(named, []);
});
