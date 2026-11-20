// PROTOTYPE CP5 (G-V4.VIEW): login, the list of stored graphs with a name filter, the drawing, what cannot be drawn marked on it (FR-48, FR-49, NFR-12).
import { visData, visOptions } from './graph-view.js';
import { filterGraphs, entryLabel } from './list-filter.js';
import { withProblemMarks } from './problems.js';

const $ = (id) => document.getElementById(id);
let graphs = [];
let network = null;
let current = null;
let chosen = null;

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
  if (!res.ok) { $('login-error').textContent = 'The name or the password is wrong.'; return; }
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

function draw() {
  const { graph, named, missing } = withProblemMarks(current.graph, current.problems);
  const { nodes, edges, problems } = visData(graph);
  for (const n of nodes) if (missing.has(n.id)) { n.group = 'missing'; n.label = `missing: ${n.id}`; }
  const dashed = new Set(current.problems.filter((p) => p.problem === 'missing_step').map((p) => p.connection));
  for (const e of edges) if (dashed.has(graph.edges[Number(e.id.slice(1))]?.id)) { e.dashes = true; e.color = { color: '#b3261e' }; }
  const options = visOptions(colors());
  options.edges.smooth = { enabled: true, type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.6 };
  options.groups.missing = { shape: 'box', color: { background: 'transparent', border: '#b3261e' }, shapeProperties: { borderDashes: [5, 5] } };
  options.physics = { enabled: true, solver: 'barnesHut', stabilization: { enabled: true, iterations: 250, fit: true } };
  network?.destroy();
  network = new vis.Network($('view'), { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, options);
  network.on('stabilizationIterationsDone', () => network.setOptions({ physics: { enabled: false } }));
  network.on('click', ({ nodes: [n], edges: [e] }) => {
    const step = n === undefined ? undefined : current.graph.nodes.find((x) => x.id === n);
    const link = e === undefined ? undefined : current.graph.edges[Number(e.slice(1))];
    $('detail').textContent = n !== undefined && !step ? `missing step "${n}"` : JSON.stringify(step ?? link ?? '', null, 2);
  });
  $('status').textContent = `${current.graph.id}, version ${current.version} of ${current.current} (${current.author}): ${nodes.length - missing.size} steps, ${edges.length} connections` + (named.length ? `; ${named.length} problem(s)` : '');
  $('problems').replaceChildren(...named.map((text) => { const li = document.createElement('li'); li.textContent = text; return li; }));
  $('detail').textContent = 'Click a step or a connection.';
}

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
