// The node-and-edge view of the Graph app (REQ-GA-001, N-5 T-01). A graph is the document of IF-104:
// {"nodes": [{"id", "kind": "process" | "data", ...}], "edges": [{"from", "to"}]}. The layout is computed here and drawn as SVG
// markup, so the page needs no library and the drawing can be checked without a browser.

const MARGIN = 60;
const NODE_W = 120;
const NODE_H = 36;

/** the graph of a document: the graph itself, or the "workflow" of a library entry (the provisional seed format of N-3.2) */
export function graphOf(entry) {
  const graph = entry && Array.isArray(entry.nodes) ? entry : entry?.workflow;
  if (!graph || !Array.isArray(graph.nodes) || !Array.isArray(graph.edges)) throw new Error('no graph: expected "nodes" and "edges" lists');
  return graph;
}

/** the layer of each node: the length of the longest path that reaches it, so every edge points to a later layer.
 *  The relaxation stops after one round per node, so a cycle (refused by the graph rules on save) still gets drawn. */
function layers(ids, edges) {
  const layer = new Map(ids.map((id) => [id, 0]));
  for (let round = 0; round < ids.length; round += 1) {
    let changed = false;
    for (const { from, to } of edges) {
      if (layer.get(to) < layer.get(from) + 1 && layer.get(from) + 1 < ids.length) {
        layer.set(to, layer.get(from) + 1);
        changed = true;
      }
    }
    if (!changed) break;
  }
  return layer;
}

/** positions of the nodes (centres) and the edges between them; edges to unknown ids are left out */
export function layout(graph, { dx = 180, dy = 80 } = {}) {
  const ids = graph.nodes.map((node) => node.id);
  const known = new Set(ids);
  const edges = graph.edges.filter((edge) => known.has(edge.from) && known.has(edge.to));
  const layer = layers(ids, edges);
  const rows = new Map();
  const nodes = graph.nodes.map((node) => {
    const l = layer.get(node.id);
    const row = rows.get(l) ?? 0;
    rows.set(l, row + 1);
    return { id: node.id, kind: node.kind, layer: l, row, x: MARGIN + l * dx, y: MARGIN + row * dy };
  });
  const at = new Map(nodes.map((node) => [node.id, node]));
  const placed = edges.map(({ from, to }) => ({ from, to, x1: at.get(from).x, y1: at.get(from).y, x2: at.get(to).x, y2: at.get(to).y }));
  const maxLayer = Math.max(0, ...nodes.map((node) => node.layer));
  const maxRow = Math.max(0, ...[...rows.values()].map((count) => count - 1));
  return { nodes, edges: placed, width: 2 * MARGIN + maxLayer * dx, height: 2 * MARGIN + maxRow * dy };
}

function escape(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

/** where a line from the centre (x1, y1) towards (x2, y2) leaves the node box, so the arrow head stays visible */
function boxExit(x1, y1, x2, y2) {
  const ddx = x2 - x1;
  const ddy = y2 - y1;
  const scale = Math.min(ddx ? (NODE_W / 2) / Math.abs(ddx) : Infinity, ddy ? (NODE_H / 2) / Math.abs(ddy) : Infinity);
  return scale === Infinity ? [x1, y1] : [x1 + ddx * scale, y1 + ddy * scale];
}

/** the SVG markup of a graph: one <g class="node"> per node (data nodes round, process nodes square) and one
 *  <line class="edge"> per edge. Ids are user text, so they are escaped. */
export function svgMarkup(graph) {
  const { nodes, edges, width, height } = layout(graph);
  const lines = edges.map(({ from, to, x1, y1, x2, y2 }) => {
    const [ax, ay] = boxExit(x1, y1, x2, y2);
    const [bx, by] = boxExit(x2, y2, x1, y1);
    return `<line class="edge" data-from="${escape(from)}" data-to="${escape(to)}" x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" marker-end="url(#arrow)"/>`;
  });
  const boxes = nodes.map(({ id, kind, x, y }) => {
    const radius = kind === 'data' ? NODE_H / 2 : 4;
    return `<g class="node ${kind === 'data' ? 'data' : 'process'}" data-id="${escape(id)}">`
      + `<rect x="${x - NODE_W / 2}" y="${y - NODE_H / 2}" width="${NODE_W}" height="${NODE_H}" rx="${radius}"/>`
      + `<text x="${x}" y="${y}">${escape(id)}</text></g>`;
  });
  const arrow = '<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
    + '<path d="M0,0 L10,5 L0,10 z"/></marker></defs>';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`
    + arrow + lines.join('') + boxes.join('') + '</svg>';
}
