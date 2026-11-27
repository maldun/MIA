// The left column's content and the history (graph_app/panel.js, history.js; R6; REQ-GA-036 to 040). Run: node --test tests/js/graph-panel.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { stepFields, connectionFields, storedText } from '../../graph_app/panel.js';
import { historyEntries, neighbour } from '../../graph_app/history.js';

test('REQ-GA-036, REQ-GA-037: a processing step shows kind, tool and trust in words', () => {
  // Example: untrusted, lifecycle null, code true -> trust untrusted, lifecycle none, changed since trusted no, holds code yes.
  // Given a processing step and its entry of IF-104 v2
  const step = { id: 's', data: { type: 'transform', toolbox_id: 'import.demo' } };
  const info = { kind: 'transform', trust: 'untrusted', lifecycle: null, reason: 'it is not in the toolbox', code: true, changed_since_trusted: false };
  // When its fields are made
  // Then each is named, labelled and in words
  assert.deepEqual(stepFields(step, 'processing', info), [['kind', 'kind', 'processing'], ['toolbox_id', 'toolbox ID', 'import.demo'], ['trust', 'trust', 'untrusted'],
    ['lifecycle', 'lifecycle', 'none'], ['reason', 'reason', 'it is not in the toolbox'], ['changed_since_trusted', 'changed since trusted', 'no'], ['code', 'holds code', 'yes']]);
});

test('REQ-GA-036: a data step and a step of another kind show their kind only', () => {
  // Example: a data step -> [kind data]; a context step with the entry {kind: concept} -> [kind concept].
  // Given a data step and a context step
  // When their fields are made
  // Then only the kind is there
  assert.deepEqual(stepFields({ id: 'd', data: { type: 'data', value: 1 } }, 'data', { kind: 'data' }), [['kind', 'kind', 'data']]);
  assert.deepEqual(stepFields({ id: 'c', data: { type: 'concept' } }, 'concept', { kind: 'concept' }), [['kind', 'kind', 'concept']]);
});

test('REQ-GA-036: a connection shows its ends and role; the stored text is the JSON as stored', () => {
  // Example: e1 a -> b, no role -> from a, to b, role none; e2 role code -> role code; the text holds "role": "code".
  // Given two connections
  const e2 = { id: 'e2', from: 'a', to: 'b', data: { role: 'code' } };
  // When their fields and text are made
  // Then the ends and role are named, none where there is no role
  assert.deepEqual(connectionFields({ id: 'e1', from: 'a', to: 'b', data: {} }).map((f) => f[2]), ['a', 'b', 'none']);
  assert.deepEqual(connectionFields(e2).map((f) => f[2]), ['a', 'b', 'code']);
  assert.ok(storedText(e2).includes('"role": "code"'));
});

test('REQ-GA-038: the history is newest first with who and when, the current one marked', () => {
  // Example: versions 1 anna t1, 2 ben t2 -> [2 ben t2 current, 1 anna t1].
  // Given two versions, oldest first as the API gives them
  // When the history is made
  const entries = historyEntries([{ version: 1, author: 'anna', time: 't1' }, { version: 2, author: 'ben', time: 't2' }], 2);
  // Then the newest is first and marked
  assert.deepEqual(entries.map((e) => [e.version, e.current, e.text]), [[2, true, 'version 2 · ben · t2 · current'], [1, false, 'version 1 · anna · t1']]);
});

test('REQ-GA-040: previous and next step one version, and nothing beyond the ends', () => {
  // Example: 1..4 from 2 -> previous 1, next 3; from 1 previous null; from 4 next null; one version -> neither.
  // Given versions 1 to 4 and a graph of one version
  const four = [1, 2, 3, 4].map((version) => ({ version }));
  // When the neighbours are asked for
  // Then they are one step away, and null at the ends
  assert.deepEqual([neighbour(four, 2, 'previous'), neighbour(four, 2, 'next'), neighbour(four, 1, 'previous'), neighbour(four, 4, 'next')], [1, 3, null, null]);
  assert.deepEqual([neighbour([{ version: 1 }], 1, 'previous'), neighbour([{ version: 1 }], 1, 'next')], [null, null]);
});
