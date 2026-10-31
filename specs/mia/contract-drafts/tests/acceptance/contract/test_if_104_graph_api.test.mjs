// IF-104 workflow and graph API (Backend to Graph app) on its HTTP routes: the contract suite runs against the JavaScript mock (stage 1) and the
// real Backend (stage 2, skipped until N-2 serves the routes). The same cases as test_if_104_graph_api.py, spoken over fetch as the page speaks.
// Protected after the Plan gate (amendment A-36). Run with: node --test "tests/acceptance/contract/test_if_104_graph_api.test.mjs"
import assert from 'node:assert/strict';
import { eachProvider } from '../../helpers/contract.mjs';
import { GraphApiMock } from '../../helpers/mocks/if_104_graph_api.mjs';

const make = (kind) => (kind === 'mock' ? new GraphApiMock() : null);
const GRAPH = {
  nodes: [{ id: 'claim', kind: 'data' }, { id: 'check', kind: 'process' }, { id: 'verdict', kind: 'data' }],
  edges: [{ from: 'claim', to: 'check' }, { from: 'check', to: 'verdict' }],
};

function edited(note) {
  const doc = structuredClone(GRAPH);
  doc.nodes[1].note = note;
  return doc;
}

/** one request as the page makes it: JSON body, the session cookie of the browser; gives { status, body } */
async function call(api, method, path, body, extra = {}) {
  const init = { method, credentials: 'same-origin', ...extra };
  if (body !== undefined) Object.assign(init, { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const response = await api.fetch(path, init);
  return { status: response.status, body: await response.json() };
}

const login = (api, user, password) => call(api, 'POST', '/api/login', { user, password });
const save = (api, kind, id, doc, expected) => call(api, 'PUT', `/api/${kind}/${id}`, expected === undefined ? { doc } : { doc, expected_version: expected });

// mark.req("IF-104", "REQ-BE-076")
eachProvider('IF-104', 'TC-IF-104-01 golden 1: version 1, an edit as version 2, the diff names the changed node, restore gives version 3 equal to version 1', make, async (api) => {
  await login(api, 'anna', 'pw-anna');
  assert.deepEqual((await save(api, 'workflows', 'lookup', GRAPH)).body, { version: 1 });
  assert.deepEqual((await save(api, 'workflows', 'lookup', edited('tighter'))).body, { version: 2 });
  assert.deepEqual((await call(api, 'GET', '/api/workflows/lookup/diff?a=1&b=2')).body.nodes_changed, ['check']);
  assert.deepEqual((await call(api, 'POST', '/api/workflows/lookup/restore', { version: 1 })).body, { version: 3 });
  assert.deepEqual((await call(api, 'GET', '/api/workflows/lookup')).body.doc, GRAPH);
  assert.deepEqual((await call(api, 'GET', '/api/workflows/lookup?version=2')).body.doc, edited('tighter'));
  assert.deepEqual((await call(api, 'GET', '/api/workflows/lookup/history')).body.map((h) => h.version), [1, 2, 3]);
  assert.deepEqual((await call(api, 'GET', '/api/workflows')).body, ['lookup']);
});

// mark.req("IF-104", "REQ-GA-007")
eachProvider('IF-104', 'TC-IF-104-02: the graph app has no login of its own; the version records the account of the backend session', make, async (api) => {
  await login(api, 'anna', 'pw-anna');
  await save(api, 'context_graphs', 'chat', GRAPH);
  await login(api, 'ben', 'pw-ben');
  await save(api, 'context_graphs', 'chat', edited('x'));
  assert.deepEqual((await call(api, 'GET', '/api/context_graphs/chat/history')).body.map((h) => h.author), ['anna', 'ben']);
});

// mark.req("IF-104", "REQ-GA-007")
eachProvider('IF-104', 'TC-IF-104-03 golden 3: wrong credentials, a made-up session and a request without the cookie are 401 and change nothing', make, async (api) => {
  const wrong = await login(api, 'anna', 'wrong');
  assert.deepEqual([wrong.status, wrong.body.error], [401, 'bad_credentials']);
  api.cookie = 'made-up';
  for (const [method, path, body] of [['GET', '/api/workflows'], ['PUT', '/api/workflows/w', { doc: GRAPH }], ['GET', '/api/workflows/w']]) {
    const answer = await call(api, method, path, body);
    assert.deepEqual([answer.status, answer.body.error], [401, 'unauthenticated'], `${method} ${path}`);
  }
  await login(api, 'anna', 'pw-anna');
  const omitted = await call(api, 'GET', '/api/workflows', undefined, { credentials: 'omit' });
  assert.deepEqual([omitted.status, omitted.body.error], [401, 'unauthenticated']);
  assert.deepEqual((await call(api, 'GET', '/api/workflows')).body, []);
});

// mark.req("IF-104", "REQ-BE-076", "REQ-GA-003")
eachProvider('IF-104', 'TC-IF-104-04 golden 2: a cycle is 422 with the rule; no id and no version appear', make, async (api) => {
  await login(api, 'anna', 'pw-anna');
  const cyc = { nodes: [{ id: 'a', kind: 'process' }, { id: 'b', kind: 'data' }], edges: [{ from: 'a', to: 'b' }, { from: 'b', to: 'a' }] };
  const refused = await save(api, 'workflows', 'bad', cyc);
  assert.deepEqual([refused.status, refused.body.error, refused.body.rule], [422, 'invalid', 'cycle']);
  const adj = { nodes: [{ id: 'a', kind: 'data' }, { id: 'b', kind: 'data' }], edges: [{ from: 'a', to: 'b' }] };
  assert.equal((await save(api, 'workflows', 'bad', adj)).body.rule, 'adjacent_data_nodes');
  const session = { nodes: [{ id: 'debate', kind: 'process', session: true }], edges: [] };
  assert.equal((await save(api, 'workflows', 'bad', session)).body.rule, 'session_stopping_criterion');
  assert.deepEqual((await call(api, 'GET', '/api/workflows')).body, []);
});

// mark.req("IF-104")
eachProvider('IF-104', 'TC-IF-104-05 golden 3: unknown id and kind are 404; a stale expected_version is 409 with the current version', make, async (api) => {
  await login(api, 'anna', 'pw-anna');
  assert.equal((await call(api, 'GET', '/api/workflows/none')).status, 404);
  const kind = await call(api, 'GET', '/api/nonsense');
  assert.deepEqual([kind.status, kind.body.error], [404, 'unknown_kind']);
  await save(api, 'workflows', 'w', GRAPH);
  await save(api, 'workflows', 'w', edited('b'));
  const stale = await save(api, 'workflows', 'w', edited('c'), 1);
  assert.deepEqual([stale.status, stale.body.error, stale.body.detail], [409, 'conflict', { current: 2 }]);
});
