// The Skill run view (REQ-FE-032, REQ-CLV-030 to 039, 043, 044; IF-101 v16): a strip with the run that the backend names. The model (skill-run-model.js) decides what is shown,
// this module draws it. Every text of a run (reason, result, answers, material, elements) goes in as a text node: nothing of it is ever markup (REQ-CLV-043).
import { applyStatus, runOfHash, controlAction, controlsModel, elementsModel, headerModel, meterModel, phaseModel, shownModel } from './skill-run-model.js';

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function initSkillRunView({ root, socket, api, t, onStop = () => {}, notify = () => {} }) {
  const $ = (id) => root.querySelector(`#${id}`);
  let view = null;      // a task_status or a run record of the run that is shown
  const fileInfo = new Map();      // file name -> the entry of the files volume

  const label = (prefix, key) => {
    const text = t(`${prefix}.${key}`);
    return text === `${prefix}.${key}` || !text ? key.replace(/_/g, ' ') : text;
  };
  const clock = (started) => {
    const date = new Date(started);
    return Number.isNaN(date.getTime()) ? String(started ?? '') : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  function drawFull(run) {
    $('srv-result').textContent = run.result ?? '';
    $('srv-answers').replaceChildren(...(run.answers ?? []).map((a) => el('li', '', a.text)));
    $('srv-material').replaceChildren(...(run.material ?? []).map((m) => el('li', '', typeof m === 'string' ? m : m?.title ?? JSON.stringify(m))));
    $('srv-files').replaceChildren(...(run.files ?? []).map((name) => {
      const item = el('li');
      const link = el('a', '', name);
      link.href = `/api/files/${encodeURIComponent(name)}`;
      item.append(link);
      const info = fileInfo.get(name);      // size, time and task, when the files volume lists the file (REQ-CLV-024); the name and the download do not wait for it
      if (info) item.append(el('span', 'srv-file-meta', [info.size !== undefined ? `${info.size} B` : '', info.time ?? '', info.task ?? ''].filter(Boolean).join(' · ')));
      return item;
    }));
    $('srv-counts').textContent = Object.entries(run.counts ?? {}).map(([key, value]) => `${label('task.count', key)}: ${value}`).join(', ');
  }

  function draw() {
    $('srv-empty').hidden = view !== null;
    $('srv-run').hidden = view === null;
    if (view === null) return;
    const header = headerModel(view, t);
    $('srv-header').textContent = `${header.skill} · ${clock(header.started)}`;
    $('srv-state').textContent = t(`srv.state.${header.state}`);
    $('srv-state').dataset.state = header.state;
    $('srv-phases').replaceChildren(...phaseModel(view.phases).map((phase) => {
      const pill = el('li', 'srv-phase', phase.name);
      pill.dataset.state = phase.state;
      pill.dataset.current = String(phase.current);
      return pill;
    }));
    const figures = meterModel(view.budget, view.counts, t);
    const figure = (className, prefix, entry) => {
      const node = el('span', className, `${label(prefix, entry.key)} ${entry.text}`);
      node.dataset.key = entry.key;
      return node;
    };
    $('srv-figures').replaceChildren(...figures.meters.map((m) => figure('srv-meter', 'task.budget', m)), ...figures.counts.map((c) => figure('srv-count', 'task.count', c)));
    const reason = $('srv-reason');
    const ended = header.state === 'failed' || header.state === 'stopped';
    reason.hidden = !(ended && (view.reason || header.state === 'stopped'));
    reason.textContent = view.reason ?? t('srv.stopped');
    const rows = [];
    for (const { label: name, text } of elementsModel(view.elements)) rows.push(el('dt', '', name), el('dd', '', text));
    $('srv-elements').replaceChildren(...rows);
    const allowed = controlsModel(header.state);
    for (const action of ['pause', 'resume', 'stop']) $(`srv-${action}`).disabled = !allowed[action];      // all three stay on the strip, the state decides which one acts (REQ-CLV-033)
    drawFull(view);
  }

  async function refresh() {
    try {
      view = shownModel(view, await api.shownRun());
    } catch (error) {
      return;      // the strip keeps what it shows; the page already says when the connection is lost
    }
    draw();
  }

  async function loadFileInfo() {
    try {
      fileInfo.clear();
      for (const file of await api.files()) fileInfo.set(file.name, file);
    } catch (error) {
      return;      // without the list the files are shown by name
    }
    if (view) drawFull(view);
  }

  /** a link of a chat message (#run=<id>) opens the Full run part of that run and brings the view into sight (REQ-CLV-037) */
  async function open(id, { quiet = false } = {}) {
    try {
      view = await api.skillRun(id);
    } catch (error) {
      if (!quiet) notify(t('workspace.failed'));
      return false;
    }
    draw();
    $('srv-full').open = true;
    root.scrollIntoView({ block: 'nearest' });
    return true;
  }
  document.addEventListener('click', (event) => {
    const link = event.target.closest?.('a[href^="#run="]');
    if (!link) return;
    event.preventDefault();
    open(runOfHash(link.getAttribute('href')));
  });

  const calls = { pause: () => api.pause().catch(() => notify(t('workspace.failed'))), resume: () => api.resume().catch(() => notify(t('workspace.failed'))), stop: () => onStop() };
  for (const action of ['pause', 'resume', 'stop']) {
    $(`srv-${action}`).addEventListener('click', () => view && controlAction(action, headerModel(view, t).state, calls));
  }

  // the panel leaves room for the strip (the layout follows in T-09)
  new ResizeObserver(() => document.documentElement.style.setProperty('--strip-h', `${root.offsetHeight}px`)).observe(root);

  socket.on('task_status', (status) => {
    view = applyStatus(view, status);
    draw();
  });
  socket.on('skill_run_changed', refresh);
  socket.on('files_changed', loadFileInfo);
  async function start() {
    const linked = runOfHash(location.hash);      // a reload keeps the link: the page opens the linked run, else the one the backend names
    // a link that cannot be opened (a deleted run, one of another account) is no reason to show nothing: the run the backend names is shown (REQ-CLV-038)
    if (!linked || !(await open(linked, { quiet: true }))) await refresh();
    loadFileInfo();
  }
  socket.on('connect', start);
  if (socket.connected) start();      // the socket may have connected before this module ran
  draw();
  return { refresh, open, shown: () => view };
}
