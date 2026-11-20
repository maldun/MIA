// PROTOTYPE: the graph app pulling a stored graph (record form) from the backend. The record form keeps the node type in data.type, the view reads kind.
// Detail panel on the left (the editor's place), vis-network physics selectable; the layered places of visData are the start and the "Layers" button.
import { visData, visOptions } from './graph-view.js';
import { toViewGraph } from './adapter.js';
if (typeof document !== 'undefined') {
  const $ = (i) => document.getElementById(i);
  const [pick, status, view, detail, physics, solver, freeze, layers, edgeStyle] = ['pick', 'status', 'view', 'detail', 'physics', 'solver', 'freeze', 'layers', 'edges'].map($);
  const style = getComputedStyle(document.documentElement), c = (n) => style.getPropertyValue(n).trim();
  const colors = { data: c('--data'), process: c('--process'), line: c('--line'), text: c('--fg') };
  let network, current;
  view.style.height = '78vh';
  const physicsOptions = () => ({
    enabled: physics.checked, solver: solver.value,
    barnesHut: { gravitationalConstant: -4000, springLength: 110, springConstant: 0.04, avoidOverlap: 0.4 },
    forceAtlas2Based: { gravitationalConstant: -60, springLength: 110, avoidOverlap: 0.4 },
    repulsion: { nodeDistance: 130, springLength: 110 },
    hierarchicalRepulsion: { nodeDistance: 130, springLength: 110 },
    stabilization: { enabled: true, iterations: 250, fit: true },
  });
  // rounded edges: a bezier curve that leaves a node sideways fits the left-to-right layers; the others are for comparison
  const smooth = () => edgeStyle.value === 'straight' ? false
    : edgeStyle.value === 'cubicBezier' ? { enabled: true, type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.6 }
    : edgeStyle.value === 'curvedCW' ? { enabled: true, type: 'curvedCW', roundness: 0.2 } : { enabled: true, type: edgeStyle.value };
  const apply = () => network?.setOptions({ physics: physicsOptions() });
  const draw = () => {
    const { nodes, edges, problems } = visData(toViewGraph(current));
    network?.destroy();
    network = new vis.Network(view, { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, (() => { const o = visOptions(colors); return { ...o, edges: { ...o.edges, smooth: smooth() }, physics: physicsOptions() }; })());
    network.on('click', ({ nodes: [n] }) => { detail.textContent = n === undefined ? '' : JSON.stringify(current.nodes.find((x) => x.id === n), null, 2); });
    // settle, then hold still so a dragged node stays where it is dropped (the stored positions of the real app are a side record, D-363)
    network.on('stabilizationIterationsDone', () => { if (freeze.checked) network.setOptions({ physics: { enabled: false } }); });
    status.textContent = `${current.id}: ${nodes.length} nodes, ${edges.length} edges${problems.length ? '; not drawn: ' + problems.join('; ') : ''}`;
  };
  const show = async (id) => {
    current = await (await fetch(`/proto/graphs/${encodeURIComponent(id)}`, { credentials: 'same-origin' })).json();
    draw();
  };
  const ids = await (await fetch('/proto/graphs')).json();
  pick.replaceChildren(...ids.map((i) => new Option(i, i)));
  pick.onchange = () => show(pick.value);
  physics.onchange = solver.onchange = () => { freeze.checked = false; apply(); };
  edgeStyle.onchange = () => network?.setOptions({ edges: { smooth: smooth() } });
  // settings menu: opens under its button, closes with Escape, a click outside or the button again
  const button = $('settings-button'), menu = $('settings');
  const setOpen = (open) => { menu.hidden = !open; button.setAttribute('aria-expanded', String(open)); };
  button.onclick = () => setOpen(menu.hidden);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !menu.hidden) { setOpen(false); button.focus(); } });
  document.addEventListener('click', (e) => { if (!menu.hidden && !menu.contains(e.target) && e.target !== button) setOpen(false); });
  layers.onclick = () => { physics.checked = false; draw(); };      // back to the computed layers: same picture every time
  if (ids.length) show(ids[0]);
}
