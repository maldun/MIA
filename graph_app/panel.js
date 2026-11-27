// The left column's content (R6, written again for REQ-GA-036, 037, 044 and the hooks of page-interface-note.md section 2). Pure: values
// in, [name, label, value] out; the page puts them in as text only (REQ-GA-029).

const word = (v) => (v === true ? 'yes' : v === false ? 'no' : v === null || v === undefined || v === '' ? 'none' : String(v));

/** the known values of a step: its kind, the tool of a processing or loop-controlling step, and for such a step of a workflow graph its
 *  trust, lifecycle, reason, whether it changed since trusted and whether it holds code (REQ-GA-036, 037) */
export function stepFields(step, kind, info) {
  const rows = [['kind', 'kind', kind]];
  if (step.data?.toolbox_id !== undefined) rows.push(['toolbox_id', 'toolbox ID', step.data.toolbox_id]);
  if (info && (info.kind === 'transform' || info.kind === 'master') && 'trust' in info) {
    rows.push(['trust', 'trust', info.trust], ['lifecycle', 'lifecycle', info.lifecycle], ['reason', 'reason', info.reason],
      ['changed_since_trusted', 'changed since trusted', info.changed_since_trusted], ['code', 'holds code', info.code]);
  }
  return rows.map(([name, label, value]) => [name, label, word(value)]);
}

/** the known values of a connection: its ends and its role */
export function connectionFields(edge) {
  return [['from', 'from', edge.from], ['to', 'to', edge.to], ['role', 'role', edge.data?.role]].map(([name, label, value]) => [name, label, word(value)]);
}

/** the full stored text of a step or a connection */
export const storedText = (item) => JSON.stringify(item, null, 2);
