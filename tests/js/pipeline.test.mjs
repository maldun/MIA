// The status block behind an answer: node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { pipelineRows, pipelineLine, pipelineState, pipelineHeadline } from '../../templates/static/chat/chat-model.js';

const t = (key, vars = {}) => key + (vars.n !== undefined ? `:${vars.n}:${vars.s}` : '');

const start = (node, plain, playful = '', item = null) => ({ kind: 'start', node, plain, playful, item });
const done = (node, item = null) => ({ kind: 'done', node, item });

test('one row per step, in order, with the state of its last event', () => {
  const events = [{ kind: 'run_start', payload: { show: true } }, start('plan', 'planning', 'Pondering…'), done('plan'),
    start('search', 'searching', 'Rummaging…'), { kind: 'retry', node: 'search', plain: 'search again' }, start('write', 'writing')];
  const rows = pipelineRows(events);
  assert.deepEqual(rows.map((r) => [r.node, r.state]), [['plan', 'done'], ['search', 'retry'], ['write', 'running']]);
  assert.equal(rows[1].plain, 'search again');
});

test('items of a map are separate rows', () => {
  const rows = pipelineRows([start('check', 'claim 1', '', 0), start('check', 'claim 2', '', 1), done('check', 0)]);
  assert.deepEqual(rows.map((r) => [r.item, r.state]), [[0, 'done'], [1, 'running']]);
});

test('errors without a node (a budget) get their own row', () => {
  const rows = pipelineRows([start('a', 'x'), { kind: 'error', node: null, plain: 'budget exceeded: steps' }]);
  assert.equal(rows.length, 2);
  assert.equal(rows[1].state, 'error');
});

test('the line is the playful text with the accurate one in brackets', () => {
  assert.equal(pipelineLine({ playful: 'Rummaging…', plain: 'search: 3 queries' }), 'Rummaging… (search: 3 queries)');
  assert.equal(pipelineLine({ playful: '', plain: 'search: 3 queries' }), 'search: 3 queries');
});

test('the headline shows the current step, then the summary', () => {
  const running = [start('plan', 'planning', 'Pondering…'), done('plan'), start('search', 'searching', 'Rummaging…')];
  assert.equal(pipelineHeadline(running, t), 'Rummaging… (searching)');
  assert.equal(pipelineHeadline([], t), 'pipeline.working');
  const finished = [...running, done('search'), { kind: 'run_end', payload: { status: 'done', seconds: 12.34 } }];
  assert.deepEqual(pipelineState(finished), { finished: true, status: 'done', seconds: 12.34 });
  assert.equal(pipelineHeadline(finished, t), 'pipeline.summary:2:12.3');
  const stopped = [...running, { kind: 'run_end', payload: { status: 'budget', seconds: 3 } }];
  assert.equal(pipelineHeadline(stopped, t), 'pipeline.summary:2:3.0 · pipeline.status.budget');
});
