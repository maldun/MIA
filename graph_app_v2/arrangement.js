// PROTOTYPE CP7 (G-V4.VIEW, FR-52): the arrangement of a graph. The layered places of the view are the reset; a saved arrangement (one per graph, the same for everyone)
// is used when there is one; otherwise the graph settles by itself. Pure helpers, tested without a browser.

/** the nodes with the saved places applied; a step without a saved place keeps its layered place; `fixed` says that every step has a place (no physics needed) */
export function applyPositions(nodes, positions) {
  if (!positions || !Object.keys(positions).length) return { nodes, fixed: false };
  let all = true;
  const placed = nodes.map((n) => {
    const p = positions[n.id];
    if (!p) { all = false; return n; }
    return { ...n, x: p.x, y: p.y };
  });
  return { nodes: placed, fixed: all };
}

/** {id: {x, y}} of the places vis reports, as whole numbers, for the saved arrangement */
export function positionsOf(places) {
  const out = {};
  for (const [id, p] of Object.entries(places ?? {})) out[id] = { x: Math.round(p.x), y: Math.round(p.y) };
  return out;
}

/** what the owner is told about the arrangement in use */
export function arrangementNote(saved, mode) {
  if (mode === 'layers') return 'Layered arrangement (reset); the saved arrangement is unchanged.';
  if (saved?.positions) return `Saved arrangement (version ${saved.version}, ${saved.author}).`;
  return 'No saved arrangement: the graph settles by itself.';
}
