// The arrangement of a graph (R6, written again for REQ-GA-030, 032, 033). Pure helpers, tested without a browser.

/** the nodes with their places: a place the owner moved the step to wins over the saved one; such a step is held there (`fixed`);
 *  a step without a place is left to the solver; places of steps the graph does not have are ignored */
export function placed(nodes, saved, moved) {
  return nodes.map((n) => {
    const p = moved?.[n.id] ?? saved?.[n.id];
    return p ? { ...n, x: p.x, y: p.y, fixed: true } : n;
  });
}

/** the nodes with a whole-number `level` each, so that every connection goes from a lower to a higher level (REQ-GA-033); no place is held.
 *  A connection that closes a cycle (a stored graph may hold one) is left out of the layering, so the levels stay finite. */
export function layered(nodes, edges) {
  const ids = nodes.map((n) => n.id);
  const out = new Map(ids.map((id) => [id, []]));
  for (const e of edges) if (out.has(e.from) && out.has(e.to)) out.get(e.from).push(e.to);
  const state = new Map();
  const order = [];
  const forward = new Map(ids.map((id) => [id, []]));
  const visit = (id) => {
    state.set(id, 'open');
    for (const next of out.get(id)) {
      if (state.get(next) === 'open') continue;                 // back to a step on the path: the connection closes a cycle
      forward.get(id).push(next);
      if (!state.has(next)) visit(next);
    }
    state.set(id, 'done');
    order.push(id);
  };
  for (const id of ids) if (!state.has(id)) visit(id);
  const level = new Map(ids.map((id) => [id, 0]));
  for (const id of order.reverse()) for (const next of forward.get(id)) level.set(next, Math.max(level.get(next), level.get(id) + 1));
  return nodes.map(({ x, y, fixed, ...n }) => ({ ...n, level: level.get(n.id) }));
}
