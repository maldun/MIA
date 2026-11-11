// The model of the Skill run view (REQ-CLV-030 to 034, 039, 044; IF-101 v16): pure helpers, no DOM, so node tests them (tests/js/skill-run-model.test.mjs).
// Interface note: specs/mia/goals/G-V3.PANEL/skill-run-view-interface-note.md.
import { budgetText } from './task-card-model.js';

const ENDED = ['done', 'failed', 'stopped'];
const FIRST_METERS = ['seconds', 'searches'];                    // Time and Searches come first, the other budgets after them
const NO_BUTTONS = { pause: false, resume: false, stop: false };

const skillName = (skill) => (skill && typeof skill === 'object' ? skill.id : skill);

function stateOf(run) {
  if (run.state) return run.state;
  return run.done ? 'done' : run.paused ? 'paused' : 'running';  // a task_status of today has no `state`
}

/** {skill, started, state} for a run record or a task_status */
export function headerModel(run, t) {
  return { skill: skillName(run.skill), started: run.started, state: stateOf(run) };
}

/** [{name, state, current}] in order, at most one current (the running phase), none after the end; [] without phases */
export function phaseModel(phases) {
  return (phases ?? []).map(({ name, state }) => ({ name, state, current: state === 'running' }));
}

/** {meters: [{key, text}], counts: [{key, text}]}: Time and Searches first as used / limit, then the other budgets, the counts after them */
export function meterModel(budget, counts, t) {
  const keys = Object.keys(budget ?? {});
  const ordered = [...FIRST_METERS.filter((key) => keys.includes(key)), ...keys.filter((key) => !FIRST_METERS.includes(key))];
  return {
    meters: ordered.map((key) => ({ key, text: budgetText(key, budget[key]) })),
    counts: Object.entries(counts ?? {}).map(([key, value]) => ({ key, text: String(value) })),
  };
}

/** the view state after a task_status: the status itself, but a status of the same run after the end changes nothing */
export function applyStatus(view, status) {
  const ended = view && (view.done || ENDED.includes(view.state));
  if (ended && view.id === status.id && !(status.done || ENDED.includes(status.state))) return view;
  return status;
}

/** {pause, resume, stop}: which buttons the state allows; all false without a run or after the end */
export function controlsModel(state) {
  if (state === 'running') return { pause: true, resume: false, stop: true };
  if (state === 'paused') return { pause: false, resume: true, stop: true };
  return { ...NO_BUTTONS };
}

/** presses a button: calls api[action]() once if the state allows it and returns true, else calls nothing and returns false */
export function controlAction(action, state, api) {
  if (!controlsModel(state)[action]) return false;
  api[action]();
  return true;
}

/** the run the view draws after a naming of the backend (a run record or null) */
export function shownModel(current, naming) {
  return naming ?? null;
}

/** [{label, text}] as text only, [] when none */
export function elementsModel(elements) {
  return (elements ?? []).map(({ label, text }) => ({ label: String(label), text: String(text) }));
}
