// PROTOTYPE CP8 (G-V4.EDIT): the working copy of a graph and the changes the owner makes to it (FR-68), and the form for the known fields of a step (FR-92).
// Round 05 CP21: the editor knows no kind of graph. Node types, their fields, start contents and checks, and the fields of a connection come from the
// profile of the graph's kind in the backend's answer to GET /api/v2/kinds (graph_profiles_proto.py); see there for the field descriptions.
// Pure: every function takes a graph and returns a new one (the stored graph is never touched); errors come back as text for the owner.

const copy = (g) => JSON.parse(JSON.stringify(g));

/** {editable, reason, profile}: what the editor may do with a graph of this kind; an unknown kind or a kind without a profile is not editable */
export function profileOf(kindsAnswer, kind) {
  const entry = kindsAnswer?.kinds?.[kind ?? 'workflow'];
  if (!entry) return { editable: false, reason: `${kindsAnswer?.unknown_reason ?? 'The program does not know this kind of graph.'} (${kind})`, profile: null };
  return { editable: Boolean(entry.editable), reason: entry.editable ? null : entry.reason, profile: entry };
}

const typeOf = (profile, type) => (profile?.node_types ?? []).find((t) => t.type === type) ?? null;

/** the words for a type of node, or 'unknown' */
export const typeName = (profile, type) => typeOf(profile, type)?.name ?? 'unknown';

/** [{type, name}] for the "add a step" choice */
export const nodeTypes = (profile) => (profile?.node_types ?? []).map((t) => ({ type: t.type, name: t.name }));

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

/** {graph, error}: the graph with a new step of the type given, with the start content of its profile */
export function addStep(graph, id, type, profile) {
  const t = typeOf(profile, type);
  const problem = nameProblem(graph, id) ?? (t ? null : 'Unknown kind of step.');
  if (problem) return { graph, error: problem };
  const next = copy(graph);
  next.nodes.push({ id, data: copy(t.start) });
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

const getPath = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
function setPath(obj, path, value) {
  const keys = path.split('.');
  let o = obj;
  for (const k of keys.slice(0, -1)) { if (typeof o[k] !== 'object' || o[k] === null) o[k] = {}; o = o[k]; }
  o[keys[keys.length - 1]] = value;
}
const top = (path) => path.split('.')[0];

const parseJson = (text) => { try { return { value: JSON.parse(text) }; } catch { return { error: 'This is not valid JSON.' }; } };
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

/** the text a field shows for a stored value */
function shown(field, value) {
  if (value === undefined || value === null) return '';
  return field.input === 'json' ? JSON.stringify(value) : String(value);
}

/** {value} or {error} or {} (empty, not set): the stored value of one field from what the owner typed or chose */
function read(field, raw) {
  const text = String(raw ?? '').trim();
  if (field.input === 'json') {
    if (!text) return {};
    const r = parseJson(text);
    if (r.error) return r;
    if (field.object && !isObject(r.value)) return { error: 'This must be a JSON object.' };
    return { value: r.value };
  }
  if (field.input === 'number') {
    if (!text) return {};
    const n = Number(text);
    const above = field.above ?? -Infinity;
    if (!Number.isFinite(n) || n <= above || (field.whole && !Number.isInteger(n))) return { error: field.whole ? `A whole number from ${Math.floor(above) + 1}.` : `A number above ${above}.` };
    return { value: n };
  }
  if (field.required && !text) return { error: field.message ?? 'This field needs a value.', value: '' };
  if (field.input === 'choice' && field.options && !field.options.includes(text)) return { error: `One of: ${field.options.filter(Boolean).join(', ')}.` };
  if (!text) return field.required ? { value: '' } : {};
  return { value: text };
}

/** the form of a step: [{...field, value}] for the known fields of its type, and `other` (the rest of the stored fields as JSON text) */
export function formFor(step, profile) {
  const data = step.data ?? {};
  const t = typeOf(profile, data.type);
  const fields = (t?.fields ?? []).map((f) => ({ ...f, value: shown(f, getPath(data, f.name)) }));
  const known = new Set(['type', ...fields.map((f) => top(f.name))]);
  const rest = Object.fromEntries(Object.entries(data).filter(([k]) => !known.has(k)));
  return { fields, other: Object.keys(rest).length ? JSON.stringify(rest, null, 2) : '' };
}

/** {data, errors: {fieldName: text}}: the stored fields that the form describes; a field the form does not know goes through `other` as JSON text */
export function applyForm(step, values, otherText = '', profile) {
  const type = (step.data ?? {}).type;
  const t = typeOf(profile, type);
  const data = { type };
  const errors = {};
  for (const f of t?.fields ?? []) {
    const r = read(f, values[f.name]);
    if (r.error) errors[f.name] = r.error;
    if ('value' in r) setPath(data, f.name, r.value);
  }
  for (const need of t?.need_one_of ?? []) {
    const any = need.fields.some((n) => getPath(data, n) !== undefined);
    if (!any && !need.fields.some((n) => errors[n])) errors[need.fields[0]] = need.message;
  }
  const known = new Set(['type', ...(t?.fields ?? []).map((f) => top(f.name))]);
  if (otherText.trim()) {
    const r = parseJson(otherText);
    if (r.error || !isObject(r.value)) errors.other = r.error ?? 'This must be a JSON object.';
    else for (const [k, v] of Object.entries(r.value)) { if (known.has(k)) errors.other = `"${k}" is set by the form.`; else data[k] = v; }
  }
  return { data, errors };
}

function connectionData(stored, values, profile) {
  const data = { ...(stored ?? {}) };
  for (const f of profile?.connection_fields ?? []) {
    if (!(f.name in values)) continue;
    const r = read(f, values[f.name]);
    if (r.error) return { error: `${f.label}: ${r.error}` };
    if ('value' in r && r.value !== '') setPath(data, f.name, r.value); else delete data[f.name];
  }
  return { data };
}

/** {graph, error}: a new connection from one step to another, with the values of the profile's connection fields that are set */
export function addConnection(graph, from, to, values = {}, profile = null) {
  const ids = new Set(graph.nodes.map((n) => n.id));
  if (!ids.has(from) || !ids.has(to)) return { graph, error: 'Both ends must be steps of the graph.' };
  const r = connectionData({}, values, profile);
  if (r.error) return { graph, error: r.error };
  const next = copy(graph);
  next.edges.push({ id: nextConnectionId(graph), from, to, data: r.data });
  return { graph: next, error: null };
}

export function removeConnection(graph, id) {
  const next = copy(graph);
  next.edges = next.edges.filter((e) => e.id !== id);
  return next;
}

/** {graph, error}: the graph with the changed known fields of a connection; its other stored fields stay */
export function changeConnection(graph, id, values, profile) {
  if (!graph.edges.some((e) => e.id === id)) return { graph, error: `There is no connection "${id}".` };
  const next = copy(graph);
  const link = next.edges.find((e) => e.id === id);
  const r = connectionData(link.data, values, profile);
  if (r.error) return { graph, error: r.error };
  link.data = r.data;
  return { graph: next, error: null };
}

/** the entries of a choice list that match the field's filter (every key equal) and what was typed (every word in the id); the order given */
export function filterTools(tools, text, filter = {}) {
  const words = String(text ?? '').toLowerCase().split(/\s+/).filter(Boolean);
  return (tools ?? []).filter((t) => Object.entries(filter).every(([k, v]) => t[k] === v) && words.every((w) => t.id.toLowerCase().includes(w)));
}

/** the line that names a tool in the list */
export const toolLabel = (t) => `${t.id}  (${t.trust}, ${t.lifecycle})`;
