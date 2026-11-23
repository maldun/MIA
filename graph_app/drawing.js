// The drawing on the vendored vis-network (G-V4.VIEW, page-interface-note.md section 3) and the browser's read-only test hook
// (`window.graphViewTest`, TR-VIEW-010, 013). Colours and the font come from the design tokens as the browser resolves them (REQ-GA-016);
// one fixed seed and solver settle a graph the same way on every opening (REQ-GA-031); a dropped step is held where it was dropped (REQ-GA-032).
import { layered } from './arrangement.js';

const SMOOTH = { rounded: { enabled: true, type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.6 }, straight: false };

/** a CSS value resolved by the browser, e.g. var(--text) -> rgb(...): vis-network draws on a canvas and does not read CSS variables */
function resolved(doc, prop, value) {
  const probe = doc.createElement('span');
  probe.style.setProperty(prop, value);
  doc.body.append(probe);
  const out = getComputedStyle(probe).getPropertyValue(prop);
  probe.remove();
  return out;
}

function tokens(doc) {
  const colour = (name) => resolved(doc, 'color', `var(${name})`);
  return { text: colour('--text'), muted: colour('--text-muted'), fill: colour('--glass-solid'), border: colour('--text-muted'), accent: colour('--accent'),
    danger: colour('--danger'), font: resolved(doc, 'font-family', 'var(--font-sans)') };
}

/** the loop-controlling step: vis draws the label of its own hexagon outside the shape, so the hexagon is drawn around its text here */
function hexagon(t, dashed) {
  return ({ ctx, x, y, state, label }) => {
    const lines = String(label ?? '').split('\n');
    ctx.font = `14px ${t.font}`;
    const lineHeight = 17, width = Math.max(...lines.map((l) => ctx.measureText(l).width)) + 44, height = lines.length * lineHeight + 20, tip = Math.min(18, height / 2);
    return {
      drawNode() {
        ctx.save();
        ctx.beginPath();
        [[x - width / 2, y], [x - width / 2 + tip, y - height / 2], [x + width / 2 - tip, y - height / 2], [x + width / 2, y], [x + width / 2 - tip, y + height / 2],
          [x - width / 2 + tip, y + height / 2]].forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
        ctx.closePath();
        ctx.fillStyle = t.fill;
        ctx.fill();
        ctx.lineWidth = state?.selected ? 3 : 1;
        ctx.strokeStyle = dashed ? t.danger : state?.selected ? t.accent : t.border;
        if (dashed) ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = t.text;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        lines.forEach((line, i) => ctx.fillText(line, x, y - ((lines.length - 1) * lineHeight) / 2 + i * lineHeight));
        ctx.restore();
      },
      nodeDimensions: { width, height },
    };
  };
}

/** a node of the page (section 3) as vis-network takes it; untrusted and missing steps get a dashed border */
function visNode(n, t) {
  const dashed = n.missing || n.marks.includes('untrusted');
  const node = { id: n.id, label: n.label, font: { color: n.missing ? t.muted : t.text, face: t.font, multi: false },
    color: { background: t.fill, border: dashed ? t.danger : t.border, highlight: { background: t.fill, border: t.accent } },
    shapeProperties: { borderDashes: dashed ? [4, 3] : false }, borderWidth: 1, borderWidthSelected: 3, margin: 10 };
  if (n.shape === 'hexagon') Object.assign(node, { shape: 'custom', ctxRenderer: hexagon(t, dashed) });
  else node.shape = n.shape;
  for (const key of ['x', 'y', 'level']) if (n[key] !== undefined) node[key] = n[key];
  if (n.fixed) node.fixed = true;
  return node;
}

/** start places for the solver: the steps without a place begin in their layer, left to right, so a workflow settles reading from left to
 *  right instead of in a tall column the view must zoom far out for; the solver only relaxes them from there (deterministic, REQ-GA-031) */
function startPlaces(nodes, edges) {
  const level = Object.fromEntries(layered(nodes, edges).map((n) => [n.id, n.level]));
  const rank = {};
  return nodes.map((n) => {
    if (n.x !== undefined) return n;
    const l = level[n.id];
    rank[l] = (rank[l] ?? 0) + 1;
    return { ...n, x: l * 220, y: (rank[l] % 2 ? 1 : -1) * Math.floor(rank[l] / 2) * 110 };
  });
}

function visOptions(o, t) {
  const layered = o.layout === 'layered';
  return {
    layout: { randomSeed: o.seed, improvedLayout: true, hierarchical: layered ? { enabled: true, direction: 'LR', sortMethod: 'directed', levelSeparation: 220 } : { enabled: false } },
    physics: { enabled: o.physics && !layered, solver: o.solver, stabilization: { enabled: true, iterations: 400, fit: true },
      barnesHut: { gravitationalConstant: -2500, springLength: 140, avoidOverlap: 0.6 } },
    edges: { arrows: { to: { enabled: true } }, smooth: SMOOTH[o.edges] ?? SMOOTH.rounded, color: { color: t.muted, highlight: t.accent }, font: { color: t.muted, face: t.font } },
    interaction: { hover: true, keyboard: false, selectConnectedEdges: false },
  };
}

export function visDrawing(container, vis, win = globalThis) {
  const doc = container.ownerDocument;
  let nodes = new vis.DataSet();
  const network = new vis.Network(container, { nodes, edges: new vis.DataSet() }, {});
  let options = {};
  let colours = tokens(doc);
  let dragEnd = () => {};
  let stabilized = () => {};
  let select = () => {};
  const hook = { settled: false };

  const settle = () => {
    hook.settled = true;
    network.setOptions({ physics: { enabled: false } });      // still from here on: a settled graph keeps its places (REQ-GA-031, 032)
    stabilized();
  };
  network.on('stabilizationIterationsDone', settle);
  network.on('dragEnd', ({ nodes: dragged }) => {
    for (const id of dragged) {
      const { x, y } = network.getPosition(id);
      nodes.update({ id, x, y, fixed: true });
      dragEnd({ id, x, y });
    }
  });
  network.on('click', ({ nodes: picked, edges: links }) => select(picked[0] ? { step: picked[0] } : links[0] ? { connection: links[0] } : {}));
  win.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change', () => { colours = tokens(doc); drawing.show(drawing.data, options); });

  const drawing = {
    data: { nodes: [], edges: [] },
    show(data, o) {
      drawing.data = data;
      options = { ...o };
      hook.settled = false;
      network.setOptions(visOptions(options, colours));
      const settling = options.physics && options.layout !== 'layered';
      nodes = new vis.DataSet((settling ? startPlaces(data.nodes, data.edges) : data.nodes).map((n) => visNode(n, colours)));
      // setData stabilizes once when physics is on (and fires stabilizationIterationsDone); a second stabilize() here would move the steps
      // again after `settled` was reported, so a step read or dragged in between would jump (found by TC-GA-037)
      network.setData({ nodes, edges: new vis.DataSet(data.edges.map((e) => ({ id: e.id, from: e.from, to: e.to, dashes: Boolean(e.dashes) }))) });
      if (!settling) win.setTimeout(settle, 0);
    },
    setOptions(o) {
      const switchedOn = o.physics === true && !options.physics;
      options = { ...options, ...o };
      network.setOptions({ edges: { smooth: SMOOTH[options.edges] ?? SMOOTH.rounded } });
      // settle again only when the arrangement is switched on, and without moving the view: the places the owner sees stay (REQ-GA-032, TC-GA-037)
      if (switchedOn && options.layout !== 'layered') {
        hook.settled = false;
        network.setOptions({ physics: { enabled: true, stabilization: { enabled: true, iterations: 400, fit: false } } });
        network.stabilize(400);
      }
    },
    positions() {
      return Object.fromEntries(Object.entries(network.getPositions()).map(([id, p]) => [id, { x: Math.round(p.x), y: Math.round(p.y) }]));
    },
    onDragEnd(fn) { dragEnd = fn; },
    onStabilized(fn) { stabilized = fn; },
    /** the owner's click in the picture: {step}, {connection} or {} for empty space (added to section 3 in T-12, see the log) */
    onSelect(fn) { select = fn; },
  };

  win.graphViewTest = Object.assign(hook, {
    positions: () => drawing.positions(),
    domPosition(id) {
      const p = network.canvasToDOM(network.getPosition(id));
      const box = container.getBoundingClientRect();
      return { x: box.left + p.x, y: box.top + p.y };
    },
    labels: () => Object.fromEntries(nodes.get().map((n) => [n.id, n.label])),
    labelColour: () => colours.text,
  });
  return drawing;
}
