// Mock of IF-104 v2, the graph API of the stored form for the Graph app (protected, amendment A-171). Complexity 2: a fake REST server behind
// a fake fetch, the JavaScript twin of if_104_v2_graph_api.py (same accounts, owner, toolbox, three rules, entries, errors), so the page of N-5
// is tested on the routes it really calls. The session is the cookie mia_session of the login (IF-101 v1): the mock plays the browser's cookie
// jar in `cookie`. A change from another Origin (header `Origin` given and not this.origin) is 403 bad_origin, as the real guard.
// Fidelity: see the Python mock (three rules of IF-301 v4 only, no record checks, a fixed toolbox, a counter for the time); a place is rounded
// half up here and half to even in Python, so no contract case uses a half.
// Test setup (not routes): seed(graph, author) stores a version; `unreachable = true` makes the store fail.
const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const clone = (x) => structuredClone(x);
export const TOOLBOX = { 'check.number': ['trusted', 'tested'], 'control.loop': ['trusted', 'tested'], 'tool.a': ['trusted', 'draft'] };
const OPS = ['add_step', 'remove_step', 'change_step', 'add_connection', 'remove_connection', 'change_connection'];
const RULE_TEXT = {
  step_identity: 'a step ID is used more than once',
  connection_endpoints: 'a connection names a step the graph does not have',
  cycle: 'the connections form a cycle',
};

class ApiError extends Error {
  constructor(status, code, fields = {}) {
    super(`${status} ${code}`);
    Object.assign(this, { status, code, fields });
  }
}

const link = (e) => ({ from: e.from, to: e.to, data: clone(e.data ?? {}) });

/** JSON with sorted keys, so two values compare as Python compares dicts */
function stable(x) {
  if (Array.isArray(x)) return `[${x.map(stable).join(',')}]`;
  if (isObject(x)) return `{${Object.keys(x).sort().map((k) => `${JSON.stringify(k)}:${stable(x[k])}`).join(',')}}`;
  return JSON.stringify(x ?? null);
}
const same = (a, b) => stable(a) === stable(b);

export function canonical(graph) {
  const byId = (a, b) => (String(a.id) < String(b.id) ? -1 : String(a.id) > String(b.id) ? 1 : 0);
  return stable({
    description: graph.description ?? null,
    nodes: graph.nodes.map((n) => ({ id: n.id, data: n.data ?? {} })).sort(byId),
    edges: graph.edges.map((e) => ({ id: e.id, from: e.from, to: e.to, data: e.data ?? {} })).sort(byId),
  });
}

export function problemsOf(graph) {
  const seen = new Map();
  for (const n of graph.nodes) seen.set(n.id, (seen.get(n.id) ?? 0) + 1);
  const found = [...seen].filter(([, c]) => c > 1).map(([step]) => ({ problem: 'duplicate_step', step }));
  for (const e of graph.edges) {
    for (const end of ['from', 'to']) if (!seen.has(e[end])) found.push({ problem: 'missing_step', connection: e.id, step: e[end], end });
  }
  return found;
}

export function ruleReport(graph) {
  const out = [];
  const ids = new Set();
  const twice = [];
  for (const n of graph.nodes) {
    if (ids.has(n.id) && !twice.includes(n.id)) twice.push(n.id);
    ids.add(n.id);
  }
  if (twice.length) out.push({ rule: 'step_identity', parts: twice, text: RULE_TEXT.step_identity });
  const loose = graph.edges.filter((e) => !ids.has(e.from) || !ids.has(e.to)).map((e) => e.id);
  if (loose.length) out.push({ rule: 'connection_endpoints', parts: loose, text: RULE_TEXT.connection_endpoints });
  if (!twice.length && !loose.length) {
    const cycle = findCycle(graph.nodes.map((n) => n.id), graph.edges);
    if (cycle) out.push({ rule: 'cycle', parts: cycle, text: RULE_TEXT.cycle });
  }
  return out;
}

function findCycle(ids, edges) {
  const out = new Map(ids.map((i) => [i, []]));
  for (const e of edges) out.get(e.from).push(e.to);
  const state = new Map();
  const stack = [];
  const visit = (i) => {
    state.set(i, 1);
    stack.push(i);
    for (const j of out.get(i)) {
      if (state.get(j) === 1) return [...stack.slice(stack.indexOf(j)), j];
      if (!state.has(j)) { const f = visit(j); if (f) return f; }
    }
    stack.pop();
    state.set(i, 2);
    return null;
  };
  for (const i of ids) if (!state.has(i)) { const f = visit(i); if (f) return f; }
  return null;
}

function applyChange(graph, c) {
  const g = clone(graph);
  const nodes = new Map(g.nodes.map((n) => [n.id, n]));
  const edges = new Map(g.edges.map((e) => [e.id, e]));
  const t = c.target;
  if (c.op === 'add_step' && !nodes.has(t)) g.nodes.push({ id: t, data: clone(c.after) });
  else if (c.op === 'remove_step' && nodes.has(t)) {
    g.nodes = g.nodes.filter((n) => n.id !== t);
    g.edges = g.edges.filter((e) => e.from !== t && e.to !== t);
  } else if (c.op === 'change_step' && nodes.has(t)) nodes.get(t).data = clone(c.after);
  else if (c.op === 'add_connection' && !edges.has(t)) g.edges.push({ id: t, ...link(c.after) });
  else if (c.op === 'remove_connection' && edges.has(t)) g.edges = g.edges.filter((e) => e.id !== t);
  else if (c.op === 'change_connection' && edges.has(t)) Object.assign(edges.get(t), link(c.after));
  else throw new Error(`${c.op} ${t} does not fit`);
  return g;
}

export function derive(before, after) {
  const bn = new Map(before.nodes.map((n) => [n.id, n]));
  const an = new Map(after.nodes.map((n) => [n.id, n]));
  const be = new Map(before.edges.map((e) => [e.id, e]));
  const ae = new Map(after.edges.map((e) => [e.id, e]));
  const gone = [...bn.keys()].filter((i) => !an.has(i));
  const out = [];
  for (const [i, e] of be) {
    if (!ae.has(i) && !gone.includes(e.from) && !gone.includes(e.to)) out.push({ op: 'remove_connection', target: i, before: link(e), after: null, reason: null });
  }
  for (const i of gone) {
    out.push({ op: 'remove_step', target: i, before: clone(bn.get(i).data ?? {}), after: null, reason: null,
      connections: [...be].filter(([, e]) => e.from === i || e.to === i).map(([k, e]) => ({ id: k, ...link(e) })) });
  }
  for (const [i, n] of an) if (!bn.has(i)) out.push({ op: 'add_step', target: i, before: null, after: clone(n.data ?? {}), reason: null });
  for (const [i, n] of an) {
    if (bn.has(i) && !same(bn.get(i).data ?? {}, n.data ?? {})) out.push({ op: 'change_step', target: i, before: clone(bn.get(i).data ?? {}), after: clone(n.data ?? {}), reason: null });
  }
  for (const [i, e] of ae) {
    if (!be.has(i)) out.push({ op: 'add_connection', target: i, before: null, after: link(e), reason: null });
    else if (!same(link(be.get(i)), link(e))) out.push({ op: 'change_connection', target: i, before: link(be.get(i)), after: link(e), reason: null });
  }
  return out;
}

const finite = (x) => typeof x === 'number' && Number.isFinite(x);
const wholeNumber = (x) => Number.isInteger(x);
const trimmed = (r) => (typeof r === 'string' && r.trim() ? r.trim() : null);
const CHANGES = new Set(['POST', 'PUT']);

export class GraphApiV2Mock {
  constructor({ accounts = { anna: 'pw-anna', ben: 'pw-ben' }, origin = 'https://mia.local', store = 'files' } = {}) {
    this.accounts = accounts;
    this.owner = Object.keys(accounts)[0];                // the first account is the owner
    this.origin = origin;
    this.store = store;
    this.unreachable = false;
    this.cookie = null;
    this.requests = [];                                   // every request as { method, path, query, body }, for tests of the consumer
    this._sessions = new Map();
    this._graphs = new Map();
    this._arrangements = new Map();
    this._changes = new Map();
    this._tick = 0;
  }

  /** test setup: stores `graph` (stored form, local IDs) as a new version by `author`; returns the version */
  seed(graph, author) { return this._put(graph.id, clone(graph), author); }

  fetch = async (input, init = {}) => {
    const url = new URL(String(input), this.origin);
    const method = (init.method ?? 'GET').toUpperCase();
    let body;
    try { body = init.body === undefined ? undefined : JSON.parse(init.body); } catch { body = undefined; }
    this.requests.push({ method, path: url.pathname, query: Object.fromEntries(url.searchParams), body });
    const headers = new Headers(init.headers ?? {});
    try {
      const answer = this._route(method, url, body ?? {}, init.credentials === 'omit' ? null : this.cookie, headers.get('Origin'));
      return new Response(JSON.stringify(answer), { status: 200, headers: { 'Content-Type': 'application/json' } });
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      return new Response(JSON.stringify({ error: error.code, ...error.fields }), { status: error.status, headers: { 'Content-Type': 'application/json' } });
    }
  };

  _route(method, url, body, session, origin) {
    if (method === 'POST' && url.pathname === '/api/login') return this._login(body.user, body.password);
    const parts = url.pathname.split('/').slice(1).map(decodeURIComponent);      // ['api', 'v2', 'graphs', id, action]
    if (parts[0] !== 'api' || parts[1] !== 'v2') throw new ApiError(404, 'not_found');
    if (!this._sessions.has(session)) throw new ApiError(401, 'unauthenticated');
    const user = this._sessions.get(session);
    if (CHANGES.has(method) && origin && origin !== this.origin) throw new ApiError(403, 'bad_origin');
    const [, , what, id, action] = parts;
    if (what === 'me' && method === 'GET' && parts.length === 3) return { user, owner: user === this.owner };
    if (what === 'store' && method === 'GET' && parts.length === 3) {
      const reachable = !this.unreachable;
      return { store: this.store, reachable, shown: 'live', live_reachable: reachable, lag: { graphs: 0, since: null } };
    }
    if (what !== 'graphs') throw new ApiError(404, 'not_found');
    const owner = CHANGES.has(method);
    if (owner && user !== this.owner) throw new ApiError(403, 'not_owner');
    if (this.unreachable) throw new ApiError(503, 'store_unreachable');
    if (parts.length === 3 && method === 'GET') return this._list();
    if (parts.length === 4 && method === 'GET') {
      const raw = url.searchParams.get('version');
      return this._read(id, raw === null ? undefined : Number(raw));
    }
    if (parts.length === 4 && method === 'PUT') return this._save(user, id, body);
    if (parts.length === 5 && method === 'GET' && action === 'versions') return this._versions(id).map(({ version, author, time }) => ({ version, author, time }));
    if (parts.length === 5 && method === 'GET' && action === 'arrangement') { this._versions(id); return clone(this._arrangements.get(id) ?? { positions: null }); }
    if (parts.length === 5 && method === 'GET' && action === 'changes') return this._changesOf(id);
    if (parts.length === 5 && method === 'POST' && action === 'check') return { rules: ruleReport(this._sent(id, body.graph)) };
    if (parts.length === 5 && method === 'POST' && action === 'restore') return this._restore(user, id, body);
    if (parts.length === 5 && method === 'PUT' && action === 'arrangement') return this._saveArrangement(user, id, body.positions);
    throw new ApiError(404, 'not_found');
  }

  _login(user, password) {
    if (!Object.hasOwn(this.accounts, user) || this.accounts[user] !== password) throw new ApiError(401, 'bad_credentials');
    const token = `s${this._sessions.size + 1}`;
    this._sessions.set(token, user);
    this.cookie = token;
    return { ok: true };
  }

  _now() {
    this._tick += 1;
    const two = (n) => String(n).padStart(2, '0');
    return `2026-01-01T00:${two(Math.floor(this._tick / 60))}:${two(this._tick % 60)}Z`;
  }

  _put(id, graph, author) {
    const versions = this._graphs.get(id) ?? [];
    versions.push({ version: versions.length + 1, author, time: this._now(), graph });
    this._graphs.set(id, versions);
    return versions.length;
  }

  _versions(id) {
    if (!this._graphs.has(id)) throw new ApiError(404, 'not_found');
    return this._graphs.get(id);
  }

  _entry(id, version) {
    const versions = this._versions(id);
    if (version === undefined) return versions.at(-1);
    if (!wholeNumber(version) || version < 1 || version > versions.length) throw new ApiError(404, 'not_found', { detail: 'version' });
    return versions[version - 1];
  }

  _sent(id, g) {
    const stored = this._entry(id).graph;
    if (!isObject(g) || !Array.isArray(g.nodes) || !Array.isArray(g.edges)) throw new ApiError(422, 'invalid', { detail: 'graph' });
    const out = Object.fromEntries(Object.entries(stored).filter(([k]) => !['nodes', 'edges', 'description'].includes(k)).map(([k, v]) => [k, clone(v)]));
    return { ...out, description: g.description ?? stored.description, nodes: clone(g.nodes), edges: clone(g.edges) };
  }

  _steps(graph) {
    const code = new Set(graph.edges.filter((e) => e.data?.role === 'code').map((e) => e.to));
    const out = {};
    for (const n of graph.nodes) {
      const data = n.data ?? {};
      const info = { kind: data.type ?? 'unknown' };
      if ((graph.kind ?? 'workflow') === 'workflow' && ['transform', 'master'].includes(info.kind)) {
        const known = Object.hasOwn(TOOLBOX, data.toolbox_id ?? '');
        const [trust, lifecycle] = known ? TOOLBOX[data.toolbox_id] : ['untrusted', null];
        Object.assign(info, { trust, lifecycle, reason: known ? 'it is in the toolbox' : 'it is not in the toolbox', code: code.has(n.id), changed_since_trusted: false });
      }
      out[n.id] = info;
    }
    return out;
  }

  _list() {
    return [...this._graphs.keys()].sort().map((id) => {
      const head = this._graphs.get(id).at(-1);
      const g = head.graph;
      return { id, kind: g.kind ?? 'workflow', version: head.version, author: head.author, time: head.time, description: g.description ?? null,
        steps: g.nodes.length, connections: g.edges.length };
    });
  }

  _read(id, version) {
    const entry = this._entry(id, version);
    const graph = clone(entry.graph);
    return { graph, version: entry.version, current: this._graphs.get(id).length, author: entry.author, time: entry.time,
      problems: problemsOf(graph), steps: this._steps(graph) };
  }

  _changesOf(id) {
    return this._versions(id).map((e) => {
      const rec = this._changes.get(`${id}\u0000${e.version}`);
      return rec ? { version: e.version, ...clone(rec) } : { version: e.version, kind: 'before_the_record', author: e.author, time: e.time, entries: [] };
    });
  }

  _record(id, fromVersion, version, kind, entries, author) {
    this._changes.set(`${id}\u0000${version}`, { from_version: fromVersion, kind, author, time: this._entry(id, version).time,
      entries: entries.map((e, i) => ({ n: i + 1, ...e })) });
  }

  _save(user, id, body) {
    const current = this._entry(id);
    const sent = this._sent(id, body.graph);
    if (body.expected_version !== undefined && body.expected_version !== null && body.expected_version !== current.version) {
      throw new ApiError(409, 'conflict', { current: current.version });
    }
    const broken = ruleReport(sent);
    if (broken.length) throw new ApiError(422, 'rules_broken', { rules: broken });
    let entries;
    let kind;
    if (body.changes !== undefined && body.changes !== null) {
      let replayed;
      try {
        if (!Array.isArray(body.changes) || body.changes.some((c) => !isObject(c) || !OPS.includes(c.op))) throw new Error('not entries');
        replayed = body.changes.reduce(applyChange, current.graph);
      } catch {
        throw new ApiError(422, 'changes_do_not_match');
      }
      if (canonical({ ...replayed, description: sent.description }) !== canonical(sent)) throw new ApiError(422, 'changes_do_not_match');
      entries = body.changes.map((c) => ({ op: c.op, target: c.target, before: c.before ?? null, after: c.after ?? null, reason: trimmed(c.reason) }));
      kind = 'editor';
    } else {
      entries = derive(current.graph, sent);
      kind = 'derived';
    }
    if (canonical(sent) === canonical(current.graph)) return { version: current.version, changed: false, logged: null, entries: entries.length };
    const version = this._put(id, sent, user);
    this._record(id, current.version, version, kind, entries, user);
    return { version, changed: true, logged: true, entries: entries.length };
  }

  _restore(user, id, body) {
    const current = this._entry(id);
    const old = this._entry(id, body.version).graph;
    if (canonical(old) === canonical(current.graph)) return { version: current.version, restored: body.version, changed: false };
    const version = this._put(id, clone(old), user);
    this._record(id, current.version, version, 'restore', [{ op: 'restore', target: body.version, before: null, after: null, reason: trimmed(body.reason) }], user);
    return { version, restored: body.version, changed: true };
  }

  _saveArrangement(user, id, positions) {
    const steps = new Set(this._entry(id).graph.nodes.map((n) => n.id));
    if (!isObject(positions)) throw new ApiError(422, 'invalid', { detail: 'positions' });
    const kept = {};
    for (const [step, xy] of Object.entries(positions)) {
      if (!steps.has(step)) continue;
      if (!isObject(xy) || !finite(xy.x) || !finite(xy.y)) throw new ApiError(422, 'invalid', { detail: step });
      kept[step] = { x: Math.round(xy.x), y: Math.round(xy.y) };
    }
    const version = (this._arrangements.get(id)?.version ?? 0) + 1;
    this._arrangements.set(id, { positions: kept, version, author: user, time: this._now() });
    return { version, saved: Object.keys(kept).length };
  }
}
