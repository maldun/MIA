// The model of the Skill run view (REQ-CLV-030 to 034, 039, 044; IF-101 v16): pure helpers, no DOM, so node tests them (tests/js/skill-run-model.test.mjs).
// STUB of Plan Step 4 (interface note specs/mia/goals/G-V3.PANEL/skill-run-view-interface-note.md): every function throws until Implement writes it.

const notWritten = (name) => () => { throw new Error(`not written: ${name}`); };

/** {skill, started, state} for a run record or a task_status */
export const headerModel = notWritten('headerModel');
/** [{name, state, current}] in order, at most one current (the running phase), none after the end; [] without phases */
export const phaseModel = notWritten('phaseModel');
/** {meters: [{key, text}], counts: [{key, text}]}: Time and Searches first as used / limit, then the other budgets, the counts after them */
export const meterModel = notWritten('meterModel');
/** the view state after a task_status: the status itself, but a status of the same run after done changes nothing */
export const applyStatus = notWritten('applyStatus');
/** {pause, resume, stop}: which buttons the state allows; all false without a run or after the end */
export const controlsModel = notWritten('controlsModel');
/** presses a button: calls api[action]() once if the state allows it and returns true, else calls nothing and returns false */
export const controlAction = notWritten('controlAction');
/** the run the view draws after a naming of the backend (a run record or null) */
export const shownModel = notWritten('shownModel');
/** [{label, text}] as text only, [] when none */
export const elementsModel = notWritten('elementsModel');
