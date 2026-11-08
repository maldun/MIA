// The model of the Skill run view: header, phases, meters, controls, the run that is shown, elements as text (G-V3.PANEL, IF-101 v16).
// TC-CLV-030, 031, 032, 033, 034, 039 and 044 (the model part of the checks that also run in the browser).  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { applyStatus, controlAction, controlsModel, elementsModel, headerModel, meterModel, phaseModel, shownModel }
  from '../../templates/static/chat/skill-run-model.js';

const t = (key) => key;
const STARTED = '2026-11-08T10:00:00Z';

test('TC-CLV-030: the header shows the skill, the start time and the state in turn: running, paused, done, failed, stopped', () => {
  // Given: the stand-in skill review started at a known time
  const run = (state) => ({ skill: 'review', version: '1', started: STARTED, state });
  // When: the view shows it while it runs, is paused, ends done, a second run fails and a third is stopped
  const headers = ['running', 'paused', 'done', 'failed', 'stopped'].map((state) => headerModel(run(state), t));
  // Then: the header shows review, the start time and the states in turn
  assert.deepEqual(headers, ['running', 'paused', 'done', 'failed', 'stopped'].map((state) => ({ skill: 'review', started: STARTED, state })));
  // And: a task_status names the skill as {id, version}: the same header
  assert.deepEqual(headerModel({ skill: { id: 'review', version: '1' }, started: STARTED, state: 'running' }, t), { skill: 'review', started: STARTED, state: 'running' });
});

test('TC-CLV-031: three phases are three pills in order, the running one is current, a failed end leaves none current, no phases give no pills', () => {
  // Given: a run that declares three phases collect, rank and report
  const phases = (...states) => ['collect', 'rank', 'report'].map((name, i) => ({ name, state: states[i] }));
  // When: the second phase is running
  const running = phaseModel(phases('done', 'running', 'waiting'));
  // Then: three pills in order; the second is marked current
  assert.deepEqual(running, [{ name: 'collect', state: 'done', current: false }, { name: 'rank', state: 'running', current: true }, { name: 'report', state: 'waiting', current: false }]);
  // When: the third fails
  const failed = phaseModel(phases('done', 'done', 'failed'));
  // Then: the third is marked failed and none is current
  assert.equal(failed[2].state, 'failed');
  assert.equal(failed.filter((pill) => pill.current).length, 0);
  // And: a run that declares none shows no pills
  assert.deepEqual(phaseModel([]), []);
});

test('TC-CLV-032: Time and Searches are meters side by side with the counts, the same meters change in place, a status after done changes nothing', () => {
  // Given: a run that reports Time 40 of 600 s, Searches 3 of 20 and the counts found 12 and read 4
  const status = (searches, extra = {}) => ({ id: 'm1', state: 'running', done: false, paused: false, skill: { id: 'review', version: '1' }, started: STARTED, phases: [], elements: [],
    budget: { seconds: { used: 40, limit: 600 }, searches: { used: searches, limit: 20 } }, counts: { found: 12, read: 4 }, ...extra });
  const drawn = (view) => meterModel(view.budget, view.counts, t);
  let view = applyStatus(null, status(3));
  // Then: the Time and Searches meters show 40 s / 600 s and 3 / 20, and the counts
  assert.deepEqual(drawn(view), { meters: [{ key: 'seconds', text: '40 s / 600 s' }, { key: 'searches', text: '3 / 20' }], counts: [{ key: 'found', text: '12' }, { key: 'read', text: '4' }] });
  // When: a second task_status with the same id reports Searches 4 of 20
  view = applyStatus(view, status(4));
  // Then: the same meters change to 4 / 20
  assert.deepEqual(drawn(view).meters.map((m) => m.text), ['40 s / 600 s', '4 / 20']);
  // When: the run ends and a late status after done reports 9 of 20
  view = applyStatus(view, status(4, { state: 'done', done: true }));
  view = applyStatus(view, status(9));
  // Then: the figure after done changes nothing
  assert.deepEqual(drawn(view).meters.map((m) => m.text), ['40 s / 600 s', '4 / 20']);
});

test('TC-CLV-033: each press sends one request, the state decides which button acts, after the end no button acts', () => {
  // Given: a running scripted skill and the mock of IF-101 that counts requests
  const requests = [];
  const api = { pause: () => requests.push('pause'), resume: () => requests.push('resume'), stop: () => requests.push('stop') };
  // When: the user presses pause, then resume, then stop
  const pressed = [controlAction('pause', 'running', api), controlAction('resume', 'paused', api), controlAction('stop', 'running', api)];
  // Then: exactly one pause, one resume and one stop request reach the mock
  assert.deepEqual([pressed, requests], [[true, true, true], ['pause', 'resume', 'stop']]);
  // And: the button shows resume while paused (and pause while running)
  assert.deepEqual(controlsModel('paused'), { pause: false, resume: true, stop: true });
  assert.deepEqual(controlsModel('running'), { pause: true, resume: false, stop: true });
  // And: after the end no button acts
  for (const state of ['done', 'failed', 'stopped']) {
    assert.deepEqual(controlsModel(state), { pause: false, resume: false, stop: false });
    assert.equal(controlAction('stop', state, api), false);
  }
  assert.equal(requests.length, 3);
});

test('TC-CLV-034: the view draws the run that the backend names: A, then B, then A again with its final figures', () => {
  // Given: the mock names run A as shown, then run B, then after both ended run A again as the last one ended
  const A = { id: 'A', skill: 'lookup', state: 'running', counts: {} };
  const B = { id: 'B', skill: 'review', state: 'running', counts: {} };
  const Aended = { id: 'A', skill: 'lookup', state: 'done', counts: { found: 12 } };
  // When: the page receives each naming
  const shown = [shownModel(null, A), shownModel(A, B), shownModel(B, Aended)];
  // Then: the view shows A, then B, then A with its final figures
  assert.deepEqual(shown.map((run) => run.id), ['A', 'B', 'A']);
  assert.deepEqual(shown[2].counts, { found: 12 });
});

test('TC-CLV-039: no run named gives no run and no button', () => {
  // Given: the mock names no run
  // When: the page loads, and again after the history records were deleted and skill_run_changed arrived with no id
  const shown = [shownModel(null, null), shownModel({ id: 'A', state: 'done' }, null)];
  // Then: the view has no run to draw (it shows that no skill has run yet) and has no button
  assert.deepEqual(shown, [null, null]);
  assert.deepEqual(controlsModel(null), { pause: false, resume: false, stop: false });
});

test('TC-CLV-044: the elements of a skill are label and text pairs as text, a skill without elements has none', () => {
  // Given: a scripted skill that reports the elements Works read = 12 and Grade = B<b>x</b>, and one that reports none
  const elements = [{ label: 'Works read', text: '12' }, { label: 'Grade', text: 'B<b>x</b>' }];
  // When: the Skill run view is drawn
  const model = elementsModel(elements);
  // Then: both labels, 12 and the text B<b>x</b> are kept as characters (no markup is interpreted)
  assert.deepEqual(model, elements);
  assert.equal(typeof model[1].text, 'string');
  // And: the second skill shows only the common elements
  assert.deepEqual(elementsModel([]), []);
  assert.deepEqual(elementsModel(undefined), []);
});
