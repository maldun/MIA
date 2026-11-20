// PROTOTYPE CP5: the list of graphs and its name filter (FR-48). Pure, so it is tested without a browser.
/** the graphs whose id or description contains every word typed (case ignored), in the order given */
export function filterGraphs(graphs, text) {
  const words = String(text ?? '').toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return graphs;
  return graphs.filter((g) => { const hay = `${g.id} ${g.description ?? ''} ${g.kind ?? ''}`.toLowerCase(); return words.every((w) => hay.includes(w)); });
}

/** the label of one list entry: id, kind, version and size */
export function entryLabel(g) {
  return `${g.id}  (${g.kind === 'context' ? 'context graph' : 'workflow graph'}, v${g.version}, ${g.steps} steps, ${g.connections} connections)`;
}
