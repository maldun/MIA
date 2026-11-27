// The picture of a stored graph (graph_app/adapter.js, step-marks.js, problems.js; R6; REQ-GA-024 to 029). Run: node --test tests/js/graph-picture.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { pictureOf, labelOf } from '../../graph_app/adapter.js';
import { kindOf, marksOf, isWorkflow } from '../../graph_app/step-marks.js';
import { missingSteps, problemText } from '../../graph_app/problems.js';

const step = (id, type, more = {}) => ({ id, data: { type, ...more } });

test('REQ-GA-026: the kinds of a workflow step have their shape and word; an unknown type is a box with its type', () => {
  // Example: data -> ellipse "data"; transform -> box "processing"; master -> hexagon "loop-controlling"; "odd" -> box "odd"; none -> box "unknown".
  // Given steps of each type
  // When their kinds are read in a workflow graph
  const kinds = ['data', 'transform', 'master', 'odd', undefined].map((t) => kindOf(step('s', t), true));
  // Then each has its shape and word
  assert.deepEqual(kinds, [{ shape: 'ellipse', kind: 'data' }, { shape: 'box', kind: 'processing' }, { shape: 'hexagon', kind: 'loop-controlling' },
    { shape: 'box', kind: 'odd' }, { shape: 'box', kind: 'unknown' }]);
});

test('REQ-GA-027: marks only where attention is needed, one word each', () => {
  // Example: trusted, no code -> []; untrusted + code -> [untrusted, code]; trusted but changed -> [changed]; a data step -> [].
  // Given the step entries of IF-104 v2
  const entries = [{ kind: 'transform', trust: 'trusted', code: false, changed_since_trusted: false },
    { kind: 'transform', trust: 'untrusted', code: true, changed_since_trusted: false },
    { kind: 'master', trust: 'trusted', code: false, changed_since_trusted: true }, { kind: 'data' }, undefined];
  // When their marks are read
  // Then only untrusted, changed and code appear, each one word
  assert.deepEqual(entries.map(marksOf), [[], ['untrusted', 'code'], ['changed'], [], []]);
});

test('REQ-GA-028: a graph of another kind is drawn neutrally with its types, no marks', () => {
  // Example: kind swarm, an agent step untrusted -> box "agent", no marks; kind absent or workflow -> workflow shapes.
  // Given a swarm graph whose step the backend calls untrusted
  const shown = { graph: { id: 'w', kind: 'swarm', nodes: [step('a', 'agent')], edges: [] }, steps: { a: { kind: 'transform', trust: 'untrusted' } } };
  // When it is turned into a picture
  const { nodes } = pictureOf(shown);
  // Then the step is a neutral box with its type and no mark
  assert.deepEqual([nodes[0].shape, nodes[0].kind, nodes[0].marks], ['box', 'agent', []]);
  assert.deepEqual([isWorkflow({}), isWorkflow({ kind: 'workflow' }), isWorkflow({ kind: 'context' })], [true, true, false]);
});

test('REQ-GA-028: a step of another kind whose type is a workflow type is still a neutral box', () => {
  // Example: a context graph with steps of type data and master -> boxes "data" and "master", not an ellipse or a hexagon "loop-controlling".
  // Given a context graph whose steps have the types of workflow steps
  const shown = { graph: { id: 'c', kind: 'context', nodes: [step('d', 'data'), step('m', 'master')], edges: [] } };
  // When it is turned into a picture
  // Then both are boxes with their stored type
  assert.deepEqual(pictureOf(shown).nodes.map((n) => [n.shape, n.kind]), [['box', 'data'], ['box', 'master']]);
});

test('REQ-GA-024, REQ-GA-025: every connection has its arrow; a missing end is a marked missing step and its connection dashed', () => {
  // Example: e1 a -> b, e2 b -> gone (missing_step) -> nodes a, b, gone {missing}; e2 dashed, e1 not; both arrows 'to'.
  // Given a graph with a connection to a step it does not have
  const shown = { graph: { id: 'g', nodes: [step('a', 'data'), step('b', 'transform')], edges: [{ id: 'e1', from: 'a', to: 'b' }, { id: 'e2', from: 'b', to: 'gone' }] },
    problems: [{ problem: 'missing_step', connection: 'e2', step: 'gone', end: 'to' }], steps: {} };
  // When it is turned into a picture
  const { nodes, edges } = pictureOf(shown);
  // Then the missing step is there and marked, and only its connection is dashed
  assert.deepEqual(nodes.map((n) => [n.id, n.missing, n.kind]), [['a', false, 'data'], ['b', false, 'processing'], ['gone', true, 'missing step']]);
  assert.deepEqual(edges.map((e) => [e.id, e.arrows, e.dashes]), [['e1', 'to', false], ['e2', 'to', true]]);
});

test('REQ-GA-025: a step ID used twice is drawn once and named', () => {
  // Example: two steps "a" -> one node a; the problem reads "step a: the ID is used more than once".
  // Given a graph with the step ID a twice
  const shown = { graph: { id: 'g', nodes: [step('a', 'data'), step('a', 'transform')], edges: [] }, problems: [{ problem: 'duplicate_step', step: 'a' }] };
  // When it is turned into a picture and its problem into words
  // Then a is drawn once, as stored first, and the problem is named
  assert.deepEqual(pictureOf(shown).nodes.map((n) => [n.id, n.kind]), [['a', 'data']]);
  assert.equal(problemText(shown.problems[0]), 'step a: the ID is used more than once');
});

test('REQ-GA-025: the missing steps are named once each, in order, with the connection and its end', () => {
  // Example: e2 and e3 to gone, e4 from lost -> [gone, lost]; e4 reads "its start step lost does not exist".
  // Given three problems naming two missing steps
  const problems = [{ problem: 'missing_step', connection: 'e2', step: 'gone', end: 'to' }, { problem: 'missing_step', connection: 'e3', step: 'gone', end: 'to' },
    { problem: 'missing_step', connection: 'e4', step: 'lost', end: 'from' }];
  // When they are read
  // Then each missing step is there once, and the words name the connection and the end
  assert.deepEqual(missingSteps(problems), ['gone', 'lost']);
  assert.equal(problemText(problems[2]), 'connection e4: its start step lost does not exist');
});

test('REQ-GA-029: the label is plain text: the ID as stored, the kind and the marks', () => {
  // Example: '<img src=x>' processing, untrusted, code -> "<img src=x>\nprocessing · untrusted · code".
  // Given a hostile step ID
  // When its label is made
  // Then it holds the ID unchanged
  assert.equal(labelOf('<img src=x>', 'processing', ['untrusted', 'code']), '<img src=x>\nprocessing · untrusted · code');
});
