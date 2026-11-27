// The list of graphs and its filter (R6, written again for REQ-GA-019 and REQ-GA-020). Pure, so it is tested without a browser.

/** the graphs whose ID or description holds every typed word, case ignored, in the order given (REQ-GA-020); no word keeps all */
export function filterGraphs(graphs, text) {
  const words = String(text ?? '').toLowerCase().split(/\s+/).filter(Boolean);
  return graphs.filter((g) => {
    const hay = `${g.id} ${g.description ?? ''}`.toLowerCase();
    return words.every((w) => hay.includes(w));
  });
}

/** the text of one list entry: ID, kind, version and the counts, in the words of the page interface note (REQ-GA-019) */
export function entryLabel(g) {
  return `${g.id} · ${g.kind} · version ${g.version} · ${g.steps} steps · ${g.connections} connections`;
}
