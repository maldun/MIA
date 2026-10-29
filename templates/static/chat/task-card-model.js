// The status card of a running task (REQ-WFM-031, IF-101 v8 `task_status`): pure helpers, no DOM, so node tests them (tests/js/taskcard.test.mjs).
// The card draws whatever budgets and counts a task reports: a later task needs no change here.

function number(value) {
  return Number(value).toLocaleString('en-US', { maximumFractionDigits: 1 });
}

/** "12 s / 600 s" for seconds, "1,200 / 400,000" for the others; a budget without a limit shows the used part only */
export function budgetText(name, figures) {
  const unit = name === 'seconds' ? ' s' : '';
  const used = figures?.used === undefined ? '' : `${number(figures.used)}${unit}`;
  const limit = figures?.limit === undefined ? '' : `${number(figures.limit)}${unit}`;
  return used && limit ? `${used} / ${limit}` : used || limit;
}

function label(prefix, key, t) {
  const text = t(`${prefix}.${key}`);
  return text === `${prefix}.${key}` || !text ? key.replace(/_/g, ' ') : text;
}

/** the card as data: {title, phase, state: 'running' | 'paused' | 'done', budget: [{key, label, text, ratio}], counts: [{key, label, value}]} */
export function cardModel(status, t) {
  const budget = Object.entries(status.budget ?? {}).map(([key, figures]) => ({
    key, label: label('task.budget', key, t), text: budgetText(key, figures),
    ratio: figures?.limit ? Math.min(1, (figures.used ?? 0) / figures.limit) : null,
  }));
  const counts = Object.entries(status.counts ?? {}).map(([key, value]) => ({ key, label: label('task.count', key, t), value }));
  return {
    title: status.task, phase: status.phase ?? '', state: status.done ? 'done' : status.paused ? 'paused' : 'running', mode: status.mode ?? 'run',
    budget, counts,
  };
}

/** the same card is updated in place: the latest status of a task id wins, a status that comes late after `done` is ignored */
export function latest(previous, status) {
  if (previous?.done && !status.done) return previous;
  return status;
}
