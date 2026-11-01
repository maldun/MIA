// The node-and-edge view of the Graph app (REQ-GA-001, N-5 T-01; vis-network since D-124). A graph is the document of IF-104:
// {"nodes": [{"id", "kind": "process" | "data", ...}], "edges": [{"from", "to"}]}. This module turns it into the nodes, edges and options of
// vis-network; it touches no page, so it is tested without a browser. The places are computed here and physics is off, so the same graph is
// always drawn the same way and a node the user drags stays where it is dropped.

const DX = 180;
const DY = 80;

const isGraph = (doc) => Boolean(doc) && Array.isArray(doc.nodes) && Array.isArray(doc.edges);

/** the graphs a JSON file holds, as [{ name, graph }]: a graph itself, a library entry (its workflow and its context graph; the provisional
 *  seed format of N-3.2), a record read through IF-104 ({id, version, doc}) or a stored record file (its list of versions: the last one) */
export function graphsOf(entry) {
  const record = Array.isArray(entry) ? entry.at(-1) : entry;
  let found = [];
  if (isGraph(record)) found = [{ name: 'graph', graph: record }];
  else if (isGraph(record?.doc)) found = [{ name: `${record.id} version ${record.version}`, graph: record.doc }];
  else if (isGraph(record?.workflow)) {
    found = [{ name: 'workflow', graph: record.workflow }];
    if (isGraph(record.context_graph)) found.push({ name: 'context graph', graph: record.context_graph });
  }
  if (!found.length) throw new Error('no graph: expected "nodes" and "edges" lists');
  return found;
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

/** places of the nodes in layers (x) and rows (y). A repeated id or an edge to an unknown id is refused on save, but the graph must still
 *  be drawn so the user sees what to fix: the first node of an id and the edges between known nodes are kept, the rest is named in problems. */
export function layout(graph) {
  const problems = [];
  const unique = new Map();
  for (const node of graph.nodes) {
    if (unique.has(node.id)) problems.push(`node ${node.id}: the id is used twice`);
    else unique.set(node.id, node);
  }
  const edges = [];
  graph.edges.forEach(({ from, to }, index) => {
    if (unique.has(from) && unique.has(to)) edges.push({ index, from, to });
    else problems.push(`edge ${from}->${to}: unknown node`);
  });
  const layer = layers([...unique.keys()], edges);
  const rows = new Map();
  const nodes = [...unique.values()].map((node) => {
    const l = layer.get(node.id);
    const row = rows.get(l) ?? 0;
    rows.set(l, row + 1);
    return { id: node.id, kind: node.kind, layer: l, row, x: l * DX, y: row * DY };
  });
  return { nodes, edges, problems };
}

/** the nodes and edges for vis-network: a data node is in the group "data", every other node in "process"; an edge is an arrow with the
 *  id e<index in the document>, so a selected edge leads back to its entry. Labels are drawn as plain text on the canvas (font.multi off). */
export function visData(graph) {
  const { nodes, edges, problems } = layout(graph);
  return {
    nodes: nodes.map(({ id, kind, x, y }) => ({ id, label: String(id), group: kind === 'data' ? 'data' : 'process', x, y })),
    edges: edges.map(({ index, from, to }) => ({ id: `e${index}`, from, to, arrows: 'to' })),
    problems,
  };
}

/** the options of the vis-network view; colors = { data, process, line, text } from the page's style */
export function visOptions(colors) {
  return {
    physics: false,
    layout: { hierarchical: false },
    interaction: { dragNodes: true, dragView: true, zoomView: true, hover: true },
    nodes: { font: { color: colors.text, multi: false }, borderWidth: 1 },
    edges: { arrows: { to: { enabled: true } }, color: { color: colors.line, highlight: colors.text }, smooth: false },
    groups: {
      data: { shape: 'ellipse', color: colors.data },
      process: { shape: 'box', color: colors.process },
    },
  };
}
