// PROTOTYPE CP5 (G-V4.VIEW): login, the list of stored graphs with a name filter, the drawing, what cannot be drawn marked on it (FR-48, FR-49, NFR-12).
import { visData, visOptions } from './graph-view.js';
import { filterGraphs, entryLabel } from './list-filter.js';
import { withProblemMarks } from './problems.js';
import { groupOf, labelOf, makeHexagonRenderer } from './step-marks.js';
import { renderPanel, renderStepList } from './panel.js';
import { loadSettings, saveSettings, edgeSmooth } from './settings.js';
import { applyPositions, positionsOf, arrangementNote } from './arrangement.js';
import { historyEntries, neighbour, versionNote } from './history.js';
import { addStep, removeStep, changeStep, addConnection, removeConnection, changeConnection } from './edit-model.js';
import { renderStepEditor, renderConnectionEditor } from './edit-panel.js';
import * as hist from './undo-stack.js';
import { storeNote, canEdit } from './store-note.js';

const $ = (id) => document.getElementById(id);
let graphs = [];
let network = null;
let current = null;
let chosen = null;
let versions = [];
let saved = null;
let mode = 'auto';
let editing = false;
let draft = null;
let livePositions = null;
let isOwner = false;
let tools = [];
let history = null;
let storeStatus = null;

const viewGraph = () => (editing && draft ? draft : current.graph);
const kindOf = (id) => viewGraph().nodes.find((n) => n.id === id)?.data?.type;
const infoOf = (id) => {
  const type = kindOf(id);
  if (editing && (type === 'transform' || type === 'master')) {        // while editing the marks follow the tool chosen in the working copy
    const tool = tools.find((t) => t.id === viewGraph().nodes.find((n) => n.id === id)?.data?.toolbox_id);
    return { kind: type, trust: tool?.trust ?? 'untrusted', lifecycle: tool?.lifecycle ?? null, code: current.steps[id]?.code ?? false };
  }
  return current.steps[id] ?? { kind: type };
};
const localProblems = (graph) => { const ids = new Set(graph.nodes.map((n) => n.id)); return graph.edges.flatMap((e) => ['from', 'to'].filter((end) => !ids.has(e[end])).map((end) => ({ problem: 'missing_step', connection: e.id, step: e[end], end }))); };
const problemsOf = () => (editing ? localProblems(draft) : current.problems);
let storage = null;
try { storage = window.localStorage; } catch { storage = null; }
const settings = loadSettings(storage);

const api = async (path, options) => {
  const res = await fetch(path, { credentials: 'same-origin', ...options });
  if (res.status === 401) { show('login'); throw new Error('login needed'); }
  if (res.status === 503) { storeStatus = { split: true, live: 'unreachable', lag: null }; refreshStoreNote(); }
  return res;
};

function show(which) {
  $('login').hidden = which !== 'login';
  $('viewer').hidden = which !== 'viewer';
}

$('login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const res = await fetch('/api/login', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user: $('user').value, password: $('password').value }) });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const reasons = { bad_credentials: 'The name or the password is wrong.', throttled: 'Too many wrong tries; wait a minute.', bad_origin: 'The server refused this address (bad_origin).', insecure_channel: 'A password may only be sent over HTTPS or from this machine.' };
    $('login-error').textContent = reasons[body.error] ?? `The login failed (${res.status} ${body.error ?? ''}).`;
    return;
  }
  $('login-error').textContent = '';
  start();
});

$('logout').addEventListener('click', async () => { await fetch('/api/logout', { method: 'POST', credentials: 'same-origin' }); show('login'); });

function renderList() {
  const shown = filterGraphs(graphs, $('filter').value);
  $('list').replaceChildren(...shown.map((g) => {
    const li = document.createElement('li');
    li.textContent = entryLabel(g);                              // text, never markup
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', String(g.id === chosen));
    li.tabIndex = 0;
    li.addEventListener('click', () => open(g.id));
    li.addEventListener('keydown', (e) => { if (e.key === 'Enter') open(g.id); });
    return li;
  }));
}
$('filter').addEventListener('input', renderList);

function colors() {
  const style = getComputedStyle(document.documentElement), c = (n) => style.getPropertyValue(n).trim();
  return { data: c('--data'), process: c('--process'), line: c('--line'), text: c('--fg') };
}

async function open(id, version) {
  chosen = id;
  renderList();
  const q = version ? `?version=${version}` : '';
  if (storeStatus?.split) await loadStoreStatus();
  const [res, arr, vs] = await Promise.all([api(`/api/v2/graphs/${encodeURIComponent(id)}${q}`), api(`/api/v2/graphs/${encodeURIComponent(id)}/arrangement`), api(`/api/v2/graphs/${encodeURIComponent(id)}/versions`)]);
  current = await res.json();
  saved = await arr.json();
  versions = await vs.json();
  mode = 'auto';
  renderHistory();
  draw();
}

function renderHistory() {
  const entries = historyEntries(versions, current.version);
  const items = entries.map((e) => {
    const li = document.createElement('li');
    li.textContent = e.text;                                     // text, never markup
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', String(e.version === current.version));
    li.tabIndex = 0;
    li.addEventListener('click', () => open(chosen, e.version));
    li.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(chosen, e.version); } });
    return li;
  });
  $('history').replaceChildren(...items);
  $('prev').disabled = neighbour(versions, current.version, 'previous') === null;
  $('next').disabled = neighbour(versions, current.version, 'next') === null;
}
$('prev').addEventListener('click', () => { const v = neighbour(versions, current.version, 'previous'); if (v !== null) open(chosen, v); });
$('next').addEventListener('click', () => { const v = neighbour(versions, current.version, 'next'); if (v !== null) open(chosen, v); });

function pick(id) {
  const step = viewGraph().nodes.find((x) => x.id === id);
  if (editing) showEditor(step); else renderPanel(document, $('detail'), step, infoOf(id));
  network?.selectNodes([id]);
}

function draw() {
  const { graph, named, missing } = withProblemMarks(viewGraph(), problemsOf());
  const layered = visData(graph);
  const placed = mode === 'layers' ? { nodes: layered.nodes, fixed: true } : applyPositions(layered.nodes, editing ? livePositions : saved?.positions);
  const nodes = placed.nodes;
  const edges = layered.edges;
  for (const n of nodes) {
    n.group = missing.has(n.id) ? 'missing' : groupOf(kindOf(n.id));
    n.label = missing.has(n.id) ? `missing: ${n.id}` : labelOf(n.id, infoOf(n.id));
    if (infoOf(n.id).trust !== undefined && (infoOf(n.id).kind === 'transform' || infoOf(n.id).kind === 'master') && infoOf(n.id).trust !== 'trusted') n.shapeProperties = { borderDashes: [3, 3] };
  }
  const dashed = new Set(problemsOf().filter((p) => p.problem === 'missing_step').map((p) => p.connection));
  for (const e of edges) if (dashed.has(graph.edges[Number(e.id.slice(1))]?.id)) { e.dashes = true; e.color = { color: '#b3261e' }; }
  const options = visOptions(colors());
  options.edges.smooth = edgeSmooth(settings);
  options.interaction.keyboard = true;
  const untrusted = new Set(nodes.filter((n) => infoOf(n.id).trust !== undefined && infoOf(n.id).trust !== 'trusted' && (infoOf(n.id).kind === 'master' || infoOf(n.id).kind === 'transform')).map((n) => n.id));
  const c = colors();
  options.groups.master = { shape: 'custom', ctxRenderer: makeHexagonRenderer({ fill: c.process, line: c.line, text: c.text }, untrusted) };   // a hexagon with its name inside
  options.groups.missing = { shape: 'box', color: { background: 'transparent', border: '#b3261e' }, shapeProperties: { borderDashes: [5, 5] } };
  options.physics = { enabled: settings.physics && !placed.fixed, solver: 'barnesHut', stabilization: { enabled: true, iterations: 250, fit: true } };
  network?.destroy();
  network = new vis.Network($('view'), { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, options);
  network.on('stabilizationIterationsDone', () => network.setOptions({ physics: { enabled: false } }));
  network.on('click', ({ nodes: [n], edges: [e] }) => {
    if (n !== undefined) { const step = viewGraph().nodes.find((x) => x.id === n); if (editing && step) showEditor(step); else renderPanel(document, $('detail'), step ?? { id: n, data: { type: 'missing' } }, infoOf(n)); }
    else if (e !== undefined) { const link = viewGraph().edges[Number(e.slice(1))]; if (editing) showConnectionEditor(link); else renderPanel(document, $('detail'), link, null, true); }
    else renderPanel(document, $('detail'), null);
  });
  renderStepList(document, $('steps'), viewGraph(), Object.fromEntries(viewGraph().nodes.map((n) => [n.id, infoOf(n.id)])), pick);
  $('status').textContent = `${current.graph.id}, ${editing ? 'WORKING COPY of ' : ''}${versionNote(current.version, current.current)} (${current.author}): ${nodes.length - missing.size} steps, ${edges.length} connections` + (named.length ? `; ${named.length} problem(s)` : '') + liveNote(current.graph.id);
  $('arr-note').textContent = arrangementNote(saved, mode);
  $('problems').replaceChildren(...named.map((text) => { const li = document.createElement('li'); li.textContent = text; return li; }));
  renderPanel(document, $('detail'), null);
  if (editing && history) refreshUndo();
  $('restore').hidden = !(isOwner && !editing && current.version !== current.current);
}

// settings menu: opens under its button, closes with Escape, a click outside or the button again; every change applies at once and is remembered
const button = $('settings-button'), menu = $('settings');
const setOpen = (open) => { menu.hidden = !open; button.setAttribute('aria-expanded', String(open)); };
button.addEventListener('click', () => setOpen(menu.hidden));
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !menu.hidden) { setOpen(false); button.focus(); } });
document.addEventListener('click', (e) => { if (!menu.hidden && !menu.contains(e.target) && e.target !== button) setOpen(false); });
$('physics').checked = settings.physics;
$('edges').value = settings.edges;
$('physics').addEventListener('change', () => { settings.physics = $('physics').checked; saveSettings(storage, settings); network?.setOptions({ physics: { enabled: settings.physics } }); });
$('edges').addEventListener('change', () => { settings.edges = $('edges').value; saveSettings(storage, settings); network?.setOptions({ edges: { smooth: edgeSmooth(settings) } }); });
$('layers').addEventListener('click', () => { mode = 'layers'; if (current) draw(); });
$('use-saved').addEventListener('click', () => { mode = 'auto'; if (current) draw(); });
$('save-arr').addEventListener('click', async () => {
  if (!current || !network) return;
  const res = await api(`/api/v2/graphs/${encodeURIComponent(chosen)}/arrangement`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ positions: positionsOf(network.getPositions()) }) });
  if (res.status === 403) { $('arr-note').textContent = 'Only the owner can save an arrangement.'; return; }
  if (!res.ok) { $('arr-note').textContent = `The arrangement was not saved (${res.status}).`; return; }
  saved = await (await api(`/api/v2/graphs/${encodeURIComponent(chosen)}/arrangement`)).json();
  mode = 'auto';
  $('arr-note').textContent = arrangementNote(saved, mode);
});


function refreshUndo() { $('undo').disabled = !hist.canUndo(history); $('redo').disabled = !hist.canRedo(history); $('undo-note').textContent = hist.note(history); }
function stepHistory(fn) {
  if (!editing || !history) return;
  if (network) livePositions = positionsOf(network.getPositions());
  history = fn(history);
  draft = history.present;
  fillEnds();
  draw();
  checkRules();
  renderPanel(document, $('detail'), null);
}
$('undo').addEventListener('click', () => stepHistory(hist.undo));
$('redo').addEventListener('click', () => stepHistory(hist.redo));
document.addEventListener('keydown', (e) => {
  if (!editing || !(e.ctrlKey || e.metaKey) || ['INPUT', 'TEXTAREA'].includes(e.target?.tagName)) return;
  const key = String(e.key).toLowerCase();
  if (key === 'z' && !e.shiftKey) { e.preventDefault(); stepHistory(hist.undo); }
  else if ((key === 'z' && e.shiftKey) || key === 'y') { e.preventDefault(); stepHistory(hist.redo); }
});

const behind = () => (storeStatus?.split && storeStatus.lag > 0 ? ' - the copy shows it after the sync' : '');
const liveNote = (id) => (storeStatus?.behind?.[id] ? ` - the live store already has version ${storeStatus.behind[id].live}: sync the copy to see it` : '');
function refreshStoreNote() {
  $('store-note').textContent = storeNote(storeStatus);
  $('sync').hidden = !(isOwner && storeStatus?.split);
  $('edit-toggle').disabled = !canEdit(storeStatus);
  $('edit-toggle').title = canEdit(storeStatus) ? '' : 'The live store cannot be reached.';
  $('restore').disabled = !canEdit(storeStatus);
}
async function loadStoreStatus() {
  try { storeStatus = await (await fetch('/api/v2/status', { credentials: 'same-origin' })).json(); } catch { storeStatus = { split: true, live: 'unreachable', lag: null }; }
  refreshStoreNote();
}
$('sync').addEventListener('click', async () => {
  const res = await api('/api/v2/sync', { method: 'POST' });
  const body = await res.json();
  if (res.ok) { $('status').textContent = `Synced: ${body.versions_added} version(s) and ${body.records} record(s) added to the copy.`; await loadStoreStatus(); $('sync').classList.remove('attention'); if (chosen) await open(chosen); return; }
  $('status').textContent = res.status === 503 ? 'The live store cannot be reached: nothing was synced.' : `The sync was refused: ${JSON.stringify(body.graphs ?? body.error)}`;
});
$('restore').addEventListener('click', async () => {
  if (!current || current.version === current.current) return;
  const shown = current.version;
  const res = await api(`/api/v2/graphs/${encodeURIComponent(chosen)}/restore`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ version: shown }) });
  const body = await res.json();
  if (res.ok) {
    await loadStoreStatus();
    await open(chosen);
    $('status').textContent = body.changed
      ? `Version ${shown} was restored as version ${body.version}.${body.synced === false ? ` It is in the live store, but the copy could not be updated (${body.sync_problem}): you are looking at the copy (version ${current.version}).` : ''}`
      : `Version ${shown} has the same content as the current version (${body.version}): nothing was restored.`;
    $('sync').classList.toggle('attention', Boolean(storeStatus?.lag));
    return;
  }
  $('status').textContent = res.status === 503 ? 'The live store cannot be reached: nothing was restored.' : `The restore failed (${res.status} ${body.error ?? ''}).`;
});

// ---- editing (CP8): a working copy, the rules asked after every change, the change kept as a new version ----
const editBar = $('edit-bar');
function fillEnds() {
  for (const id of ['conn-from', 'conn-to']) {
    const select = $(id);
    select.replaceChildren(...draft.nodes.map((n) => { const o = document.createElement('option'); o.value = n.id; o.textContent = n.id; return o; }));
  }
}
function note(text) { $('edit-note').textContent = text; }

async function checkRules() {
  const res = await api(`/api/v2/graphs/${encodeURIComponent(chosen)}/check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ graph: { nodes: draft.nodes, edges: draft.edges } }) });
  if (res.status === 503) { note('The live store cannot be reached: editing is not possible now.'); $('keep').disabled = true; return; }
  const { rules } = await res.json();
  $('rules').replaceChildren(...rules.map((r) => { const li = document.createElement('li'); li.textContent = `${r.rule}: ${r.text} (${r.parts.join(', ')})`; return li; }));
  $('keep').disabled = rules.length > 0;
  note(rules.length ? `${rules.length} broken rule(s): the change cannot be kept yet.` : 'Every rule holds.');
}

function change(next) {
  if (network) livePositions = positionsOf(network.getPositions());
  history = hist.push(history, next);
  draft = history.present;
  fillEnds();
  draw();
  checkRules();
}

function showEditor(step, errors = {}) {
  renderStepEditor(document, $('detail'), step, {
    errors, tools,
    onApply: ({ data, errors: found }) => {
      if (Object.keys(found).length) { showEditor(step, found); return; }
      const r = changeStep(draft, step.id, data);
      if (r.error) note(r.error); else { change(r.graph); showEditor(r.graph.nodes.find((n) => n.id === step.id)); }
    },
    onRemove: () => { change(removeStep(draft, step.id)); renderPanel(document, $('detail'), null); },
  });
}
function showConnectionEditor(link) {
  renderConnectionEditor(document, $('detail'), link, {
    onApply: (values) => { const r = changeConnection(draft, link.id, values); if (r.error) note(r.error); else change(r.graph); },
    onRemove: () => { change(removeConnection(draft, link.id)); renderPanel(document, $('detail'), null); },
  });
}

function startEdit() {
  if (!current || current.version !== current.current) { $('status').textContent = 'Only the current version can be edited: open the current version first.'; return; }
  editing = true;
  draft = JSON.parse(JSON.stringify(current.graph));
  history = hist.create(draft);
  livePositions = network ? positionsOf(network.getPositions()) : null;
  editBar.hidden = false;
  $('edit-toggle').hidden = true;
  fillEnds();
  draw();
  checkRules();
}
function stopEdit() {
  editing = false; draft = null; history = null; editBar.hidden = true; $('edit-toggle').hidden = !isOwner; $('rules').replaceChildren();
  renderPanel(document, $('detail'), null);
}
$('edit-toggle').addEventListener('click', startEdit);
$('discard').addEventListener('click', () => { stopEdit(); draw(); });
$('add-step').addEventListener('click', () => {
  const r = addStep(draft, $('new-name').value, $('new-kind').value);
  if (r.error) { note(r.error); return; }
  $('new-name').value = '';
  change(r.graph);
});
$('add-conn').addEventListener('click', () => {
  const r = addConnection(draft, $('conn-from').value, $('conn-to').value, { role: $('conn-role').value });
  if (r.error) note(r.error); else change(r.graph);
});
$('keep').addEventListener('click', async () => {
  const res = await api(`/api/v2/graphs/${encodeURIComponent(chosen)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ graph: { nodes: draft.nodes, edges: draft.edges }, expected_version: current.version }) });
  const body = await res.json();
  if (res.ok) { stopEdit(); note(''); await loadStoreStatus(); await open(chosen); $('status').textContent = body.changed ? `Kept as version ${body.version}.${body.synced === false ? ` It is in the live store, but the copy could not be updated (${body.sync_problem}): you are looking at the copy (version ${current.version}).` : ''}` : 'Nothing had changed: no new version.'; $('sync').classList.toggle('attention', Boolean(storeStatus?.lag)); return; }
  if (res.status === 409) { note(`The graph changed meanwhile (now version ${body.current}). Nothing was overwritten; discard the changes and open it again.`); return; }
  if (res.status === 422 && body.rules) { note('The change breaks a rule and was not kept.'); $('rules').replaceChildren(...body.rules.map((r) => { const li = document.createElement('li'); li.textContent = `${r.rule}: ${r.text} (${r.parts.join(', ')})`; return li; })); return; }
  if (res.status === 503) { note('The live store cannot be reached: nothing was kept. Editing is not possible now.'); return; }
  note(`The change was not kept (${res.status} ${body.error ?? ''}).`);
});

async function start() {
  const who = await (await fetch('/api/whoami', { credentials: 'same-origin' })).json();
  if (!who.user && !who.account) { show('login'); return; }
  $('who').textContent = who.user ?? who.account;
  isOwner = (await (await api('/api/v2/me')).json()).owner;
  if (isOwner) tools = await (await api('/api/v2/toolbox')).json();
  await loadStoreStatus();
  $('edit-toggle').hidden = !isOwner || editing;
  show('viewer');
  graphs = await (await api('/api/v2/graphs')).json();
  renderList();
  if (graphs.length && !chosen) open(graphs[0].id);
}

start().catch(() => show('login'));
