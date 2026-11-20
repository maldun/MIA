// PROTOTYPE CP11 (G-V4.REPLAY, FR-76, FR-77): the changes of an editing session as entries, and how a stored version is explained. Pure.
// The shapes are those of graph_changes.py: {op, target, before, after, reason} (+ connections for remove_step).

const same = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
const link = (e) => ({ from: e.from, to: e.to, data: e.data ?? {} });

/** the changes that lead from one graph to the next, in an order in which they apply; one action of the editor gives one change (removing a step takes its connections with it) */
export function diffChanges(before, after) {
  const bn = new Map(before.nodes.map((n) => [n.id, n])), an = new Map(after.nodes.map((n) => [n.id, n]));
  const be = new Map(before.edges.map((e) => [e.id, e])), ae = new Map(after.edges.map((e) => [e.id, e]));
  const out = [];
  const gone = [...bn.keys()].filter((i) => !an.has(i));
  for (const [i, e] of be) if (!ae.has(i) && !gone.includes(e.from) && !gone.includes(e.to)) out.push({ op: 'remove_connection', target: i, before: link(e), after: null, reason: null });
  for (const i of gone) out.push({ op: 'remove_step', target: i, before: bn.get(i).data ?? {}, after: null, reason: null, connections: [...be].filter(([, e]) => e.from === i || e.to === i).map(([k, e]) => ({ id: k, ...link(e) })) });
  for (const [i, n] of an) if (!bn.has(i)) out.push({ op: 'add_step', target: i, before: null, after: n.data ?? {}, reason: null });
  for (const [i, n] of an) if (bn.has(i) && !same(bn.get(i).data, n.data)) out.push({ op: 'change_step', target: i, before: bn.get(i).data ?? {}, after: n.data ?? {}, reason: null });
  for (const [i, e] of ae) {
    if (!be.has(i)) out.push({ op: 'add_connection', target: i, before: null, after: link(e), reason: null });
    else if (!same(link(be.get(i)), link(e))) out.push({ op: 'change_connection', target: i, before: link(be.get(i)), after: link(e), reason: null });
  }
  return out;
}

/** every change of the session that is part of what would be kept: the steps of the undo stack from the start to the present (undone changes are not there) */
export const sessionChanges = (history) => [...history.past, history.present].slice(1).flatMap((g, i) => diffChanges([...history.past, history.present][i], g));

/** what identifies a change when the owner types a reason for it, so the reason stays with the change through undo and redo */
export const changeKey = (c) => JSON.stringify([c.op, c.target, c.after]);

export const withReasons = (changes, reasons) => changes.map((c) => ({ ...c, reason: (reasons.get(changeKey(c)) ?? '').trim() || null }));

const show = (v) => { const t = JSON.stringify(v); return t === undefined ? '(nothing)' : t.length > 60 ? `${t.slice(0, 57)}...` : t; };

/** the fields that differ between two contents, as "field: before → after" */
function fieldChanges(before, after) {
  const b = before ?? {}, a = after ?? {};
  return [...new Set([...Object.keys(b), ...Object.keys(a)])].filter((k) => !same(b[k], a[k])).map((k) => `${k}: ${show(b[k])} → ${show(a[k])}`);
}

/** one entry as text: what it did, with the value before and after */
export function describeChange(c) {
  const t = `"${c.target}"`;
  switch (c.op) {
    case 'add_step': return `added step ${t} (${c.after?.type ?? 'unknown'})${c.note ? `, ${c.note}` : ''}`;
    case 'remove_step': return `removed step ${t} (${c.before?.type ?? 'unknown'})${c.connections?.length ? ` with ${c.connections.length} connection(s)` : ''}`;
    case 'change_step': return `changed step ${t}: ${fieldChanges(c.before, c.after).join('; ') || 'no field differs'}`;
    case 'add_connection': return `added connection ${t}: ${c.after.from} → ${c.after.to}${c.after.data?.role ? ` (${c.after.data.role})` : ''}`;
    case 'remove_connection': return `removed connection ${t}: ${c.before.from} → ${c.before.to}`;
    case 'change_connection': return `changed connection ${t}: ${[...(c.before.from !== c.after.from || c.before.to !== c.after.to ? [`${c.before.from} → ${c.before.to} became ${c.after.from} → ${c.after.to}`] : []), ...fieldChanges(c.before.data, c.after.data)].join('; ')}`;
    case 'restore': return `restored the content of version ${c.target}`;
    default: return `unknown change ${t}`;
  }
}

/** how a stored version came about, as lines for the page; `record` is one item of /changes */
export function explain(record) {
  if (!record) return ['No record for this version.'];
  if (record.kind === 'before_the_record') return [`Version ${record.version} was made before the record of changes existed (stored by ${record.author}, ${record.time}).`];
  const head = `Version ${record.version} started from version ${record.from_version}; kept by ${record.author}, ${record.time}${record.kind === 'derived' ? '; the entries were worked out from the difference, the editor sent none' : ''}:`;
  return [head, ...record.entries.map((e) => `${e.n}. ${describeChange(e)} - ${e.reason ? `reason: ${e.reason}` : 'no reason given'}`)];
}
