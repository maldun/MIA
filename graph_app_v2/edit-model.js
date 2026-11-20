// PROTOTYPE CP8 (G-V4.EDIT): the working copy of a graph and the changes the owner makes to it (FR-68), and the form for the known fields of a step (FR-92).
// Pure: every function takes a graph and returns a new one (the stored graph is never touched); errors come back as text for the owner.

export const KINDS = { data: 'data step', transform: 'processing step', master: 'loop-controlling step' };

const copy = (g) => JSON.parse(JSON.stringify(g));

/** a name for a new step or connection is usable when it is not empty, has no slash and is not used */
export function nameProblem(graph, id) {
  if (typeof id !== 'string' || !id.trim()) return 'The name is empty.';
  if (id.includes('/')) return 'The name must not contain a slash.';
  if (graph.nodes.some((n) => n.id === id)) return `A step named "${id}" exists.`;
  return null;
}

export function nextConnectionId(graph) {
  const used = new Set(graph.edges.map((e) => e.id));
  let n = 1;
  while (used.has(`e${n}`)) n += 1;
  return `e${n}`;
}

const START = { data: () => ({ type: 'data' }), transform: () => ({ type: 'transform', toolbox_id: '' }), master: () => ({ type: 'master', toolbox_id: '', stop: { max_repetitions: 1 } }) };

/** {graph, error}: the graph with a new step of the kind given */
export function addStep(graph, id, kind) {
  const problem = nameProblem(graph, id) ?? (START[kind] ? null : 'Unknown kind of step.');
  if (problem) return { graph, error: problem };
  const next = copy(graph);
  next.nodes.push({ id, data: START[kind]() });
  return { graph: next, error: null };
}

/** the graph without the step and without every connection that touches it */
export function removeStep(graph, id) {
  const next = copy(graph);
  next.nodes = next.nodes.filter((n) => n.id !== id);
  next.edges = next.edges.filter((e) => e.from !== id && e.to !== id);
  return next;
}

/** {graph, error}: the graph with the new content of a step (its ID stays) */
export function changeStep(graph, id, data) {
  if (!graph.nodes.some((n) => n.id === id)) return { graph, error: `There is no step "${id}".` };
  const next = copy(graph);
  next.nodes.find((n) => n.id === id).data = data;
  return { graph: next, error: null };
}

/** {graph, error}: a new connection from one step to another, with an optional role and name */
export function addConnection(graph, from, to, { role, as } = {}) {
  const ids = new Set(graph.nodes.map((n) => n.id));
  if (!ids.has(from) || !ids.has(to)) return { graph, error: 'Both ends must be steps of the graph.' };
  const next = copy(graph);
  const data = {};
  if (role) data.role = role;
  if (as) data.as = as;
  next.edges.push({ id: nextConnectionId(graph), from, to, data });
  return { graph: next, error: null };
}

export function removeConnection(graph, id) {
  const next = copy(graph);
  next.edges = next.edges.filter((e) => e.id !== id);
  return next;
}

/** {graph, error}: the graph with the changed fields of a connection (role and name) */
export function changeConnection(graph, id, { role, as }) {
  if (!graph.edges.some((e) => e.id === id)) return { graph, error: `There is no connection "${id}".` };
  const next = copy(graph);
  const link = next.edges.find((e) => e.id === id);
  const data = { ...(link.data ?? {}) };
  for (const [k, v] of [['role', role], ['as', as]]) { if (v) data[k] = v; else delete data[k]; }
  link.data = data;
  return { graph: next, error: null };
}

const KNOWN = { data: ['value', 'parameters'], transform: ['toolbox_id'], master: ['toolbox_id', 'stop'] };

/** the form of a step: [{name, label, kind: 'text'|'json'|'number', value}] for its known fields, and `other` (the rest of the stored fields as JSON text) */
export function formFor(step) {
  const data = step.data ?? {};
  const fields = [];
  if (data.type === 'data') {
    fields.push({ name: 'value', label: 'value (JSON)', kind: 'json', value: data.value === undefined ? '' : JSON.stringify(data.value) });
    fields.push({ name: 'parameters', label: 'parameters (JSON object)', kind: 'json', value: data.parameters === undefined ? '' : JSON.stringify(data.parameters) });
  } else if (data.type === 'transform' || data.type === 'master') {
    fields.push({ name: 'toolbox_id', label: 'tool (toolbox entry)', kind: 'text', value: data.toolbox_id ?? '' });
  }
  if (data.type === 'master') {
    fields.push({ name: 'max_repetitions', label: 'stop after repetitions', kind: 'number', value: data.stop?.max_repetitions ?? '' });
    fields.push({ name: 'max_seconds', label: 'stop after seconds', kind: 'number', value: data.stop?.max_seconds ?? '' });
  }
  const known = new Set(['type', ...(KNOWN[data.type] ?? [])]);
  const rest = Object.fromEntries(Object.entries(data).filter(([k]) => !known.has(k)));
  return { fields, other: Object.keys(rest).length ? JSON.stringify(rest, null, 2) : '' };
}

const parseJson = (text) => { try { return { value: JSON.parse(text) }; } catch { return { error: 'This is not valid JSON.' }; } };

/** {data, errors: {fieldName: text}}: the stored fields that the form describes; a field the form does not know goes through `other` as JSON text */
export function applyForm(step, values, otherText = '') {
  const type = (step.data ?? {}).type;
  const data = { type };
  const errors = {};
  if (type === 'data') {
    for (const name of ['value', 'parameters']) {
      const text = String(values[name] ?? '').trim();
      if (!text) continue;
      const r = parseJson(text);
      if (r.error) errors[name] = r.error;
      else if (name === 'parameters' && (r.value === null || typeof r.value !== 'object' || Array.isArray(r.value))) errors[name] = 'This must be a JSON object.';
      else data[name] = r.value;
    }
  } else if (type === 'transform' || type === 'master') {
    data.toolbox_id = String(values.toolbox_id ?? '').trim();
    if (!data.toolbox_id) errors.toolbox_id = 'A processing step needs a tool.';
  }
  if (type === 'master') {
    const stop = {};
    for (const [name, whole] of [['max_repetitions', true], ['max_seconds', false]]) {
      const text = String(values[name] ?? '').trim();
      if (!text) continue;
      const n = Number(text);
      if (!Number.isFinite(n) || n <= 0 || (whole && !Number.isInteger(n))) errors[name] = whole ? 'A whole number from 1.' : 'A number above 0.';
      else stop[name] = n;
    }
    if (!Object.keys(stop).length && !errors.max_repetitions && !errors.max_seconds) errors.max_repetitions = 'A loop-controlling step needs a limit: repetitions or seconds.';
    data.stop = stop;
  }
  if (otherText.trim()) {
    const r = parseJson(otherText);
    if (r.error || r.value === null || typeof r.value !== 'object' || Array.isArray(r.value)) errors.other = r.error ?? 'This must be a JSON object.';
    else for (const [k, v] of Object.entries(r.value)) { if (k === 'type' || k in data) errors.other = `"${k}" is set by the form.`; else data[k] = v; }
  }
  return { data, errors };
}

/** the tools that match what was typed (every word in the id), for a loop-controlling step (controllers) or a processing step (the others); the order given */
export function filterTools(tools, text, controller) {
  const words = String(text ?? '').toLowerCase().split(/\s+/).filter(Boolean);
  return (tools ?? []).filter((t) => t.controller === controller && words.every((w) => t.id.toLowerCase().includes(w)));
}

/** the line that names a tool in the list */
export const toolLabel = (t) => `${t.id}  (${t.trust}, ${t.lifecycle})`;
