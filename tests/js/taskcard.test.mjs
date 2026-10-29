// The model of the status card of a running task (REQ-WFM-031, IF-101 v8): budgets as "used / limit", counts, the state, the late status after done.
// TC-WFM-031.  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { budgetText, cardModel, latest } from '../../templates/static/chat/task-card-model.js';

const t = (key) => key;

test('TC-WFM-031: a budget is shown as used / limit, seconds with a unit, big numbers grouped', () => {
  assert.equal(budgetText('seconds', { used: 12.3, limit: 600 }), '12.3 s / 600 s');
  assert.equal(budgetText('tokens', { used: 1200, limit: 4000000 }), '1,200 / 4,000,000');
  assert.equal(budgetText('calls', { used: 3 }), '3');
  assert.equal(budgetText('seconds', { limit: 60 }), '60 s');
});

test('TC-WFM-031: the card draws every budget and count the task reported, in order, with a readable fallback label', () => {
  const status = { id: 'm7', task: 'review', phase: 'searching for x', mode: 'run', paused: false, done: false,
    budget: { seconds: { used: 5, limit: 600 }, screen: { used: 4, limit: 400 } }, counts: { on_list: 5, to_process: 1, my_new_count: 2 } };
  const model = cardModel(status, t);
  assert.equal(model.state, 'running');
  assert.deepEqual(model.budget.map((b) => b.key), ['seconds', 'screen']);
  assert.equal(model.budget[1].ratio, 0.01);
  assert.deepEqual(model.counts.map((c) => [c.key, c.value]), [['on_list', 5], ['to_process', 1], ['my_new_count', 2]]);
  assert.equal(model.counts[2].label, 'my new count');                       // a count nobody has a text for still reads
});

test('TC-WFM-033: the state is paused or done, done wins', () => {
  assert.equal(cardModel({ id: 'a', task: 'x', paused: true }, t).state, 'paused');
  assert.equal(cardModel({ id: 'a', task: 'x', paused: true, done: true }, t).state, 'done');
});

test('TC-WFM-031: a status that arrives late after done does not undo the final card', () => {
  const done = { id: 'a', done: true, counts: { n: 2 } };
  assert.equal(latest(done, { id: 'a', done: false, counts: { n: 1 } }), done);
  assert.deepEqual(latest({ id: 'a', done: false }, done), done);
});
