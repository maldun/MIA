// PROTOTYPE CP5 (G-V4.VIEW): login, the list of stored graphs with a name filter, the drawing, what cannot be drawn marked on it (FR-48, FR-49, NFR-12).
import { visData, visOptions } from './graph-view.js';
import { filterGraphs, entryLabel } from './list-filter.js';
import { withProblemMarks } from './problems.js';
import { groupOf, labelOf, makeHexagonRenderer } from './step-marks.js';
import { renderPanel, renderStepList } from './panel.js';
import { loadSettings, saveSettings, edgeSmooth } from './settings.js';
import { applyPositions, positionsOf, arrangementNote } from './arrangement.js';
import { historyEntries, neighbour, versionNote } from './history.js';

const $ = (id) => document.getElementById(id);
let graphs = [];
let network = null;
let current = null;
let chosen = null;
let versions = [];
let saved = null;
let mode = 'auto';
let storage = null;
try { storage = window.localStorage; } catch { storage = null; }
const settings = loadSettings(storage);

const api = async (path, options) => {
  const res = await fetch(path, { credentials: 'same-origin', ...options });
  if (res.status === 401) { show('login'); throw new Error('login needed'); }
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
  const step = current.graph.nodes.find((x) => x.id === id);
  renderPanel(document, $('detail'), step, current.steps[id]);
  network?.selectNodes([id]);
}

function draw() {
  const { graph, named, missing } = withProblemMarks(current.graph, current.problems);
  const layered = visData(graph);
  const placed = mode === 'layers' ? { nodes: layered.nodes, fixed: true } : applyPositions(layered.nodes, saved?.positions);
  const nodes = placed.nodes;
  const edges = layered.edges;
  for (const n of nodes) {
    n.group = missing.has(n.id) ? 'missing' : groupOf(current.graph.nodes.find((x) => x.id === n.id)?.data?.type);
    n.label = missing.has(n.id) ? `missing: ${n.id}` : labelOf(n.id, current.steps[n.id]);
    if (current.steps[n.id] && (current.steps[n.id].kind === 'transform' || current.steps[n.id].kind === 'master') && current.steps[n.id].trust !== 'trusted') n.shapeProperties = { borderDashes: [3, 3] };
  }
  const dashed = new Set(current.problems.filter((p) => p.problem === 'missing_step').map((p) => p.connection));
  for (const e of edges) if (dashed.has(graph.edges[Number(e.id.slice(1))]?.id)) { e.dashes = true; e.color = { color: '#b3261e' }; }
  const options = visOptions(colors());
  options.edges.smooth = edgeSmooth(settings);
  options.interaction.keyboard = true;
  const untrusted = new Set(nodes.filter((n) => current.steps[n.id] && current.steps[n.id].trust !== 'trusted' && (current.steps[n.id].kind === 'master' || current.steps[n.id].kind === 'transform')).map((n) => n.id));
  const c = colors();
  options.groups.master = { shape: 'custom', ctxRenderer: makeHexagonRenderer({ fill: c.process, line: c.line, text: c.text }, untrusted) };   // a hexagon with its name inside
  options.groups.missing = { shape: 'box', color: { background: 'transparent', border: '#b3261e' }, shapeProperties: { borderDashes: [5, 5] } };
  options.physics = { enabled: settings.physics && !placed.fixed, solver: 'barnesHut', stabilization: { enabled: true, iterations: 250, fit: true } };
  network?.destroy();
  network = new vis.Network($('view'), { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, options);
  network.on('stabilizationIterationsDone', () => network.setOptions({ physics: { enabled: false } }));
  network.on('click', ({ nodes: [n], edges: [e] }) => {
    if (n !== undefined) { const step = current.graph.nodes.find((x) => x.id === n); renderPanel(document, $('detail'), step ?? { id: n, data: { type: 'missing' } }, current.steps[n]); }
    else if (e !== undefined) renderPanel(document, $('detail'), current.graph.edges[Number(e.slice(1))], null, true);
    else renderPanel(document, $('detail'), null);
  });
  renderStepList(document, $('steps'), current.graph, current.steps, pick);
  $('status').textContent = `${current.graph.id}, ${versionNote(current.version, current.current)} (${current.author}): ${nodes.length - missing.size} steps, ${edges.length} connections` + (named.length ? `; ${named.length} problem(s)` : '');
  $('arr-note').textContent = arrangementNote(saved, mode);
  $('problems').replaceChildren(...named.map((text) => { const li = document.createElement('li'); li.textContent = text; return li; }));
  renderPanel(document, $('detail'), null);
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

async function start() {
  const who = await (await fetch('/api/whoami', { credentials: 'same-origin' })).json();
  if (!who.user && !who.account) { show('login'); return; }
  $('who').textContent = who.user ?? who.account;
  show('viewer');
  graphs = await (await api('/api/v2/graphs')).json();
  renderList();
  if (graphs.length && !chosen) open(graphs[0].id);
}

start().catch(() => show('login'));
