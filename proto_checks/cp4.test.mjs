// PROTOTYPE CP4 checks (node --test): what the owner is told when a run is tried (FR-64)
import test from 'node:test';
import assert from 'node:assert/strict';
import { brokenLines, runMessage, parseInputs } from '../graph_app_v2/run-note.js';

test('FR-64: every broken part is one line: a rule with its parts, or an input nobody supplies', () => {
  const lines = brokenLines([{ kind: 'rule', rule: 'cycle', text: 'the steps run in a circle', parts: ['a', 'b', 'a'] }, { kind: 'input', step: 's', input: 'question' }]);
  assert.equal(lines[0], 'cycle: the steps run in a circle (a, b, a)');
  assert.match(lines[1], /step "s" reads "question".*no writer, no start value and no value given with the run/);
  assert.deepEqual(brokenLines(undefined), []);
});

test('FR-64: the owner is told that a refused run ran no step, and how many parts are broken', () => {
  assert.match(runMessage(422, { status: 'refused', broken: [1, 2] }), /Run refused: no step ran. 2 broken part/);
  assert.match(runMessage(200, { ran: ['a', 'b'] }), /stand-in steps ran in this order: a, b/);
  assert.match(runMessage(403, {}), /Only the owner/);
  assert.match(runMessage(503, {}), /cannot be reached: nothing was run/);
  assert.match(runMessage(500, { error: 'x' }), /not tried \(500 x\)/);
});

test('FR-64: start values are a JSON object or nothing; anything else is told, not sent', () => {
  assert.deepEqual(parseInputs(''), { values: {} });
  assert.deepEqual(parseInputs('{"input.text": "hi"}'), { values: { 'input.text': 'hi' } });
  assert.match(parseInputs('[1]').error, /JSON object/);
  assert.match(parseInputs('{oops').error, /not valid JSON/);
});
