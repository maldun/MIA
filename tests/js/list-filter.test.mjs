// The list of graphs and its filter (graph_app/list-filter.js, R6, REQ-GA-019, REQ-GA-020). Run: node --test tests/js/list-filter.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { filterGraphs, entryLabel } from '../../graph_app/list-filter.js';

const graphs = [
  { id: 'research.escalate', kind: 'workflow', version: 1, steps: 54, connections: 65, description: 'research with escalation' },
  { id: 'chat', kind: 'workflow', version: 3, steps: 3, connections: 2, description: 'Plain chat' },
  { id: 'lookup.context', kind: 'context', version: 2, steps: 5, connections: 4, description: null },
];

test('REQ-GA-020: every typed word must be in the ID or the description, case ignored', () => {
  // Example: "RES" -> research.escalate; "plain CHAT" -> chat; "" and "  " -> all three, in the given order; "zzz" -> none.
  // Given three graphs, one without a description
  // When the filter is given words
  // Then only graphs holding every word in ID or description stay
  assert.deepEqual(filterGraphs(graphs, 'RES').map((g) => g.id), ['research.escalate']);
  assert.deepEqual(filterGraphs(graphs, 'plain CHAT').map((g) => g.id), ['chat']);
  assert.deepEqual(filterGraphs(graphs, '').map((g) => g.id), ['research.escalate', 'chat', 'lookup.context']);
  assert.deepEqual(filterGraphs(graphs, '  ').length, 3);
  assert.deepEqual(filterGraphs(graphs, 'zzz'), []);
});

test('REQ-GA-020: the kind is not searched, only ID and description', () => {
  // Example: "workflow" matches no ID or description -> nothing; "context" -> lookup.context by its ID.
  // Given the three graphs
  // When their kinds are typed
  // Then a kind word finds a graph only through its ID or description
  assert.deepEqual(filterGraphs(graphs, 'workflow'), []);
  assert.deepEqual(filterGraphs(graphs, 'context').map((g) => g.id), ['lookup.context']);
});

test('REQ-GA-019: an entry names ID, kind, version and the counts', () => {
  // Example: lookup.context -> "lookup.context · context · version 2 · 5 steps · 4 connections".
  // Given a context graph of the list
  // When its entry is written
  // Then it names every part in the interface note's words
  assert.equal(entryLabel(graphs[2]), 'lookup.context · context · version 2 · 5 steps · 4 connections');
});
