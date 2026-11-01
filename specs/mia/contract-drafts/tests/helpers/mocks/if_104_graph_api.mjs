// Mock of IF-104, the workflow and graph API of the Backend for the Graph app (protected). Complexity 2: a fake REST server behind a fake fetch,
// the JavaScript twin of if_104_graph_api.py on its storage mock (same accounts, tokens, versions, times, graph rules and errors), so the page of
// N-5 is tested on the HTTP routes it really calls. The session is the cookie mia_session of the login (IF-101 v1): the mock plays the browser's
// cookie jar in `cookie` (a page cannot set the Cookie header itself). It does not model concurrent edits, the login throttle or logout.
const KINDS = ['workflows', 'context_graphs'];
const VALIDATED = ['workflows'];                        // as the storage mock: the graph rules are checked on write (TB-edit)
const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);

class ApiError extends Error {
  constructor(status, code, rule = null, detail = null) {
    super(`${status} ${code}${rule ? `: ${rule}` : ''}`);
    Object.assign(this, { status, code, rule, detail });
  }
}

/** the graph rules of FR-7, the mock's own copy of tests/helpers/mocks/graph_rules.py: [rule, detail] of the first broken rule, or null */
export function violation(doc) {
  const nodes = isObject(doc) ? doc.nodes : undefined;
  const edges = isObject(doc) ? doc.edges : undefined;
  if (!Array.isArray(nodes) || !Array.isArray(edges)) return ['node_identity', 'nodes and edges must be lists'];
  const byId = new Map();
  for (const node of nodes) {
    const id = isObject(node) ? node.id : undefined;
    if (!id || typeof id !== 'string' || byId.has(id) || !['process', 'data'].includes(node.kind)) return ['node_identity', id ?? null];
    byId.set(id, node);
  }
  for (const edge of edges) {
    const [a, b] = [edge?.from, edge?.to];
    if (!byId.has(a) || !byId.has(b)) return ['node_identity', `${a}->${b}`];
    if (byId.get(a).kind === 'data' && byId.get(b).kind === 'data') return ['adjacent_data_nodes', `${a}->${b}`];
    if (byId.get(a).kind === 'process' && byId.get(b).kind === 'process') return ['adjacent_process_nodes', `${a}->${b}`];
  }
  for (const [id, node] of byId) {
    if (node.kind === 'process' && node.session && !stops(node.stop || {})) return ['session_stopping_criterion', id];
  }
  const cycle = findCycle([...byId.keys()], edges);
  return cycle ? ['cycle', cycle] : null;
}

/** A session stops when it has a limit and every limit given is an integer >= 1 (JSON has no bool/int confusion: true is not a number); null = not given (A-60, D-160, D-162). */
function stops(stop) {
  if (!isObject(stop)) return false;
  const given = ['max_cycles', 'max_seconds'].map((key) => stop[key]).filter((limit) => limit !== undefined && limit !== null);
  return given.length > 0 && given.every((limit) => Number.isInteger(limit) && limit >= 1);
}

/** JSON.parse reviver: a session limit written with a fraction or an exponent (2.0, 1e0) keeps its source text, so stops() refuses it as the
 * real rules refuse a float (A-66, D-169); JavaScript would otherwise read 2.0 as the integer 2. Needs the source text of JSON.parse (Node 21+). */
function keepFloatLimits(key, value, context) {
  const limit = key === 'max_cycles' || key === 'max_seconds';
  return limit && typeof value === 'number' && /[.eE]/.test(context?.source ?? '') ? context.source : value;
}

function findCycle(ids, edges) {
  const out = new Map(ids.map((id) => [id, []]));
  for (const edge of edges) out.get(edge.from).push(edge.to);
  const state = new Map();
  const stack = [];
  const visit = (i) => {
    state.set(i, 1);
    stack.push(i);
    for (const j of out.get(i)) {
      if (state.get(j) === 1) return [...stack.slice(stack.indexOf(j)), j];
      if (!state.has(j)) { const found = visit(j); if (found) return found; }
    }
    stack.pop();
    state.set(i, 2);
    return null;
  };
  for (const i of ids) {
    if (!state.has(i)) { const found = visit(i); if (found) return found; }
  }
  return null;
}

export class GraphApiMock {
  constructor({ accounts = { anna: 'pw-anna', ben: 'pw-ben' }, origin = 'https://mia.local' } = {}) {
    this.accounts = accounts;
    this.origin = origin;
    this.cookie = null;                                   // the browser's mia_session cookie, set by a login
    this.requests = [];                                   // every request as { method, path, query, body }, for tests of the consumer
    this._sessions = new Map();
    this._rows = Object.fromEntries(KINDS.map((kind) => [kind, new Map()]));   // kind -> id -> list of versions
    this._tick = 0;
  }

  /** the fake fetch: pass it where the page expects fetch (url relative to the origin, init as for fetch); answers a Response with a JSON body */
  fetch = async (input, init = {}) => {
    const url = new URL(String(input), this.origin);
    const method = (init.method ?? 'GET').toUpperCase();
    let body;
    try { body = init.body === undefined ? undefined : JSON.parse(init.body, keepFloatLimits); } catch (error) { body = undefined; }
    this.requests.push({ method, path: url.pathname, query: Object.fromEntries(url.searchParams), body });
    try {
      const [status, answer] = this._route(method, url, body ?? {}, init.credentials === 'omit' ? null : this.cookie);
      return new Response(JSON.stringify(answer), { status, headers: { 'Content-Type': 'application/json' } });
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      const answer = { error: error.code };
      if (error.rule) answer.rule = error.rule;
      if (error.detail !== null) answer.detail = error.detail;
      return new Response(JSON.stringify(answer), { status: error.status, headers: { 'Content-Type': 'application/json' } });
    }
  };

  _route(method, url, body, session) {
    const parts = url.pathname.split('/').slice(1).map(decodeURIComponent);    // ['api', kind, id, action]
    if (method === 'POST' && url.pathname === '/api/login') return [200, this._login(body.user, body.password)];
    if (parts[0] !== 'api' || parts.length < 2 || parts.length > 4) throw new ApiError(404, 'not_found');
    const user = this._user(session);
    const [, kind, id, action] = parts;
    if (!KINDS.includes(kind)) throw new ApiError(404, 'unknown_kind');
    const number = (text) => (text === undefined || text === null ? undefined : Number(text));
    const query = (key) => number(url.searchParams.get(key) ?? undefined);
    if (parts.length === 2 && method === 'GET') return [200, [...this._rows[kind].keys()].sort()];
    if (parts.length === 3 && method === 'GET') return [200, this._get(kind, id, query('version'))];
    if (parts.length === 3 && method === 'PUT') return [200, this._put(kind, id, body.doc ?? null, user, body.expected_version ?? undefined)];
    if (action === 'history' && method === 'GET') return [200, this._versions(kind, id).map(({ version, author, time }) => ({ version, author, time }))];
    if (action === 'diff' && method === 'GET') return [200, this._diff(kind, id, query('a'), query('b'))];
    if (action === 'restore' && method === 'POST') return [200, this._put(kind, id, this._get(kind, id, number(body.version) ?? NaN).doc, user)];
    throw new ApiError(404, 'not_found');
  }

  _login(user, password) {
    if (!Object.hasOwn(this.accounts, user) || this.accounts[user] !== password) throw new ApiError(401, 'bad_credentials');
    const token = `s${this._sessions.size + 1}`;
    this._sessions.set(token, user);
    this.cookie = token;
    return { ok: true };
  }

  _user(session) {
    if (!this._sessions.has(session)) throw new ApiError(401, 'unauthenticated');
    return this._sessions.get(session);
  }

  _now() {
    this._tick += 1;
    const two = (n) => String(n).padStart(2, '0');
    return `2026-01-01T00:${two(Math.floor(this._tick / 60))}:${two(this._tick % 60)}Z`;
  }

  _versions(kind, id) {
    const versions = this._rows[kind].get(id);
    if (!versions) throw new ApiError(404, 'not_found');
    return versions;
  }

  _get(kind, id, version) {
    const versions = this._versions(kind, id);
    if (version !== undefined && !(Number.isInteger(version) && version >= 1 && version <= versions.length)) throw new ApiError(404, 'not_found');
    return structuredClone(versions[version === undefined ? versions.length - 1 : version - 1]);
  }

  /** a new version, author = the session's account; 409 for a stale expected_version, 422 with the rule for a broken graph (no version used) */
  _put(kind, id, doc, author, expectedVersion) {
    const versions = this._rows[kind].get(id) ?? [];
    if (expectedVersion !== undefined && expectedVersion !== versions.length) throw new ApiError(409, 'conflict', null, { current: versions.length });
    if (VALIDATED.includes(kind)) {
      const broken = violation(doc);
      if (broken) throw new ApiError(422, 'invalid', broken[0], broken[1]);
    }
    const entry = { id, version: versions.length + 1, author, time: this._now(), doc: structuredClone(doc) };
    this._rows[kind].set(id, [...versions, entry]);
    return { version: entry.version };
  }

  /** node ids added, removed, changed; edges added and removed as 'from->to' (sorted, as the Python mock) */
  _diff(kind, id, a, b) {
    const [oldDoc, newDoc] = [this._get(kind, id, a ?? NaN).doc, this._get(kind, id, b ?? NaN).doc];
    const nodes = (doc) => new Map((doc?.nodes ?? []).map((n) => [n.id, n]));
    const edges = (doc) => new Set((doc?.edges ?? []).map((e) => `${e.from}->${e.to}`));
    const [on, nn, oe, ne] = [nodes(oldDoc), nodes(newDoc), edges(oldDoc), edges(newDoc)];
    const sorted = (items) => [...items].sort();
    return {
      nodes_added: sorted([...nn.keys()].filter((i) => !on.has(i))),
      nodes_removed: sorted([...on.keys()].filter((i) => !nn.has(i))),
      nodes_changed: sorted([...on.keys()].filter((i) => nn.has(i) && !sameJson(on.get(i), nn.get(i)))),
      edges_added: sorted([...ne].filter((e) => !oe.has(e))),
      edges_removed: sorted([...oe].filter((e) => !ne.has(e))),
    };
  }
}

/** equal as JSON values, key order ignored (Python compares dicts that way) */
function sameJson(x, y) {
  if (Array.isArray(x) || Array.isArray(y)) return Array.isArray(x) && Array.isArray(y) && x.length === y.length && x.every((v, i) => sameJson(v, y[i]));
  if (isObject(x) && isObject(y)) {
    const keys = Object.keys(x);
    return keys.length === Object.keys(y).length && keys.every((k) => Object.hasOwn(y, k) && sameJson(x[k], y[k]));
  }
  return x === y;
}
