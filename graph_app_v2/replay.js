// PROTOTYPE CP12 (G-V4.REPLAY, FR-78): playing recorded changes back on the version they started from. Pure; the same semantics as graph_changes.py.
const clone = (x) => JSON.parse(JSON.stringify(x));

/** the graph after one change; throws an Error that names what does not fit. `earlier(n)` gives the graph of version n (a restore needs it). */
export function applyChange(graph, change, earlier) {
  const g = clone(graph), t = change.target;
  const hasNode = (id) => g.nodes.some((n) => n.id === id), hasEdge = (id) => g.edges.some((e) => e.id === id);
  switch (change.op) {
    case 'add_step': if (hasNode(t)) throw new Error(`step ${t} exists`); g.nodes.push({ id: t, data: clone(change.after) }); break;
    case 'remove_step': if (!hasNode(t)) throw new Error(`no step ${t}`); g.nodes = g.nodes.filter((n) => n.id !== t); g.edges = g.edges.filter((e) => e.from !== t && e.to !== t); break;
    case 'change_step': if (!hasNode(t)) throw new Error(`no step ${t}`); g.nodes.find((n) => n.id === t).data = clone(change.after); break;
    case 'add_connection': if (hasEdge(t)) throw new Error(`connection ${t} exists`); g.edges.push({ id: t, from: change.after.from, to: change.after.to, data: clone(change.after.data ?? {}) }); break;
    case 'remove_connection': if (!hasEdge(t)) throw new Error(`no connection ${t}`); g.edges = g.edges.filter((e) => e.id !== t); break;
    case 'change_connection': { if (!hasEdge(t)) throw new Error(`no connection ${t}`); Object.assign(g.edges.find((e) => e.id === t), { from: change.after.from, to: change.after.to, data: clone(change.after.data ?? {}) }); break; }
    case 'restore': { if (!earlier) throw new Error('a restore needs the earlier version'); const old = earlier(t); return { nodes: clone(old.nodes), edges: clone(old.edges) }; }
    default: throw new Error(`unknown change ${change.op}`);
  }
  return g;
}

/** every state of the playback: [the start, after entry 1, after entry 2, ...] */
export function states(start, entries, earlier) {
  const out = [{ nodes: clone(start.nodes), edges: clone(start.edges) }];
  for (const entry of entries) out.push(applyChange(out[out.length - 1], entry, earlier));
  return out;
}

/** the graph as text that does not depend on the order of its steps and connections */
export const canonical = (g) => JSON.stringify({ nodes: [...g.nodes].map((n) => ({ id: n.id, data: n.data ?? {} })).sort((a, b) => (a.id < b.id ? -1 : 1)), edges: [...g.edges].map((e) => ({ id: e.id, from: e.from, to: e.to, data: e.data ?? {} })).sort((a, b) => (a.id < b.id ? -1 : 1)) }, (k, v) => (v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => (a < b ? -1 : 1))) : v));
export const sameGraph = (a, b) => canonical(a) === canonical(b);

/** what the bar of the playback shows at position k of n (0 = the starting version): the text, the labels of the two buttons and whether each can be pressed */
export function playbackState(record, k, ok) {
  const n = record.entries.length;
  const note = k === 0 ? `Showing version ${record.from_version}, the starting point. Version ${record.version} is reached after ${n} change(s).`
    : k === n ? `Change ${n} of ${n}: the end of the playback. This is version ${record.version}${ok ? ', identical to the saved version.' : ', but NOT identical to the saved version.'}`
    : `Change ${k} of ${n}; ${n - k} more to reach version ${record.version}.`;
  return { note, fwdLabel: k === n ? 'End reached' : `Forward one change (${k + 1} of ${n})`, backLabel: k === 0 ? 'At the start' : 'Back one change', fwdDisabled: k === n, backDisabled: k === 0 };
}

/** what the playback says at position k of n (0 = the starting version) */
export function stepNote(k, entries, ok) {
  const n = entries.length;
  if (k === 0) return `Start: version as it was before the first change (${n} change(s) to play).`;
  const e = entries[k - 1];
  return `Change ${k} of ${n}${k === n ? (ok ? ' (last): the result is identical to the saved version.' : ' (last): the result is NOT identical to the saved version.') : ''}`;
}
