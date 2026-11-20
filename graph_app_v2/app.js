// PROTOTYPE CP5 (G-V4.VIEW): login, the list of stored graphs with a name filter, the drawing, what cannot be drawn marked on it (FR-48, FR-49, NFR-12).
import { visData, visOptions } from './graph-view.js';
import { filterGraphs, entryLabel } from './list-filter.js';
import { withProblemMarks } from './problems.js';
import { groupOf, labelOf, SHAPES } from './step-marks.js';
import { renderPanel, renderStepList } from './panel.js';
import { loadSettings, saveSettings, edgeSmooth } from './settings.js';

const $ = (id) => document.getElementById(id);
let graphs = [];
let network = null;
let current = null;
let chosen = null;
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

async function open(id) {
  chosen = id;
  renderList();
  const res = await api(`/api/v2/graphs/${encodeURIComponent(id)}`);
  current = await res.json();
  draw();
}

function pick(id) {
  const step = current.graph.nodes.find((x) => x.id === id);
  renderPanel(document, $('detail'), step, current.steps[id]);
  network?.selectNodes([id]);
}

function draw() {
  const { graph, named, missing } = withProblemMarks(current.graph, current.problems);
  const { nodes, edges } = visData(graph);
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
  options.groups.master = { shape: SHAPES.master, color: options.groups.process.color };
  options.groups.missing = { shape: 'box', color: { background: 'transparent', border: '#b3261e' }, shapeProperties: { borderDashes: [5, 5] } };
  options.physics = { enabled: settings.physics, solver: 'barnesHut', stabilization: { enabled: true, iterations: 250, fit: true } };
  network?.destroy();
  network = new vis.Network($('view'), { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, options);
  network.on('stabilizationIterationsDone', () => network.setOptions({ physics: { enabled: false } }));
  network.on('click', ({ nodes: [n], edges: [e] }) => {
    if (n !== undefined) { const step = current.graph.nodes.find((x) => x.id === n); renderPanel(document, $('detail'), step ?? { id: n, data: { type: 'missing' } }, current.steps[n]); }
    else if (e !== undefined) renderPanel(document, $('detail'), current.graph.edges[Number(e.slice(1))], null, true);
    else renderPanel(document, $('detail'), null);
  });
  renderStepList(document, $('steps'), current.graph, current.steps, pick);
  $('status').textContent = `${current.graph.id}, version ${current.version} of ${current.current} (${current.author}): ${nodes.length - missing.size} steps, ${edges.length} connections` + (named.length ? `; ${named.length} problem(s)` : '');
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
$('layers').addEventListener('click', () => { settings.physics = false; $('physics').checked = false; saveSettings(storage, settings); if (current) draw(); });

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
