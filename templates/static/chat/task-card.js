// The status cards of running tasks (REQ-WFM-031, -033; IF-101 v8). One card per task id, updated in place by the event `task_status`, with Pause / Resume and Stop; a finished card stays
// with the final figures. The task decides which budgets and counts exist, the card only draws them.
import { cardModel, latest } from './task-card-model.js';

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function initTaskCards({ list, socket, api, t, onStop = () => {}, notify = () => {} }) {
  const cards = new Map();      // task id -> {node, status}

  function draw(entry) {
    const model = cardModel(entry.status, t);
    const node = entry.node;
    node.className = `task-card ${model.state}`;
    node.dataset.taskId = entry.status.id;
    const head = el('div', 'task-card-head');
    head.append(el('strong', '', `/${model.title}`), el('span', 'task-card-phase', model.phase), el('span', 'task-card-state', t(`task.state.${model.state}`)));
    const budget = el('dl', 'task-card-budget');
    for (const line of model.budget) {
      const row = el('div', 'task-card-row');
      row.append(el('dt', '', line.label), el('dd', '', line.text));
      if (line.ratio !== null) {
        const bar = el('progress');
        bar.max = 1;
        bar.value = line.ratio;
        bar.setAttribute('aria-label', line.label);
        row.append(bar);
      }
      budget.append(row);
    }
    const counts = el('dl', 'task-card-counts');
    for (const line of model.counts) {
      const row = el('div', 'task-card-row');
      row.append(el('dt', '', line.label), el('dd', '', String(line.value)));
      counts.append(row);
    }
    const parts = [head, counts, budget];
    if (model.state !== 'done') {
      const buttons = el('div', 'task-card-buttons');
      const toggle = el('button', '', t(model.state === 'paused' ? 'task.resume' : 'task.pause'));
      toggle.type = 'button';
      toggle.addEventListener('click', async () => {
        try {
          await (model.state === 'paused' ? api.resume() : api.pause());
        } catch (error) {
          notify(t('workspace.failed'));
        }
      });
      const stop = el('button', '', t('task.stop'));
      stop.type = 'button';
      stop.addEventListener('click', () => onStop());
      buttons.append(toggle, stop);
      parts.push(buttons);
    }
    node.replaceChildren(...parts);
  }

  socket.on('task_status', (status) => {
    let entry = cards.get(status.id);
    if (!entry) {
      const node = el('section', 'task-card');
      node.setAttribute('role', 'group');
      node.setAttribute('aria-label', `/${status.task}`);
      list.append(node);
      entry = { node, status };
      cards.set(status.id, entry);
    }
    entry.status = latest(entry.status, status);
    draw(entry);
  });
  return { cards };
}
