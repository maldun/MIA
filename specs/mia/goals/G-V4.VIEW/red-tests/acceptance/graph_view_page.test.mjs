// Node checks of the graph viewer page (G-V4.VIEW Track B): TC-GA-017 to 030 of specs/mia/goals/G-V4.VIEW/test-spec.md, under TR-VIEW-002, 004, 005,
// 018, 019, 021. The page (graph_app/viewer.js, api.js; page-interface-note.md, D-443) runs on the fake DOM over the JS mock of IF-104 v2 and hands
// its pictures to a recording drawing; the checks read DOM text and that drawing, never pixels (TR-VIEW-005).
// Run with: node --test tests/acceptance/graph_view_page.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { GraphApiV2Mock } from '../helpers/mocks/if_104_v2_graph_api.mjs';
import {
  HOSTILE, seededMock, mockGet, pageWith, memoryStorage, throwingStorage, listed, textOf, fieldValue, offered, gets,
} from '../helpers/graph_view_page.mjs';

const CONTROLS = 'button,input,select,textarea,a';

test('TC-GA-017 REQ-GA-019 REQ-GA-021: the list shows every graph with kind, version and counts; choosing one draws its current version', async () => {
  // Example: cp2.multi -> "workflow", "version 4", "3 steps", "2 connections"; choosing it draws var.in, step.write (t4), var.out.
  // Given the JS mock with cp2.multi (four versions) and sample.code (one), anna logged in
  const mock = await seededMock(['cp2.multi', 'sample.code']);
  const { root, viewer, drawing } = await pageWith({ mock });
  // When the page loads its list and the owner chooses cp2.multi
  await viewer.start();
  // Then both graphs are listed, each with ID, kind, version and the counts of steps and connections
  assert.deepEqual(listed(root), ['cp2.multi', 'sample.code']);
  const multi = textOf(root, '[data-graph-id="cp2.multi"]');
  for (const part of ['cp2.multi', 'workflow', 'version 4', '3 steps', '2 connections']) assert.ok(multi.includes(part), `${part} in ${multi}`);
  const code = textOf(root, '[data-graph-id="sample.code"]');
  for (const part of ['sample.code', 'workflow', 'version 1', '7 steps', '6 connections']) assert.ok(code.includes(part), `${part} in ${code}`);
  await viewer.open('cp2.multi');
  // And the picture shows version 4: its three steps, the current version asked, step.write naming t4
  assert.deepEqual(drawing.last().data.nodes.map((n) => n.id), ['var.in', 'step.write', 'var.out']);
  assert.ok(textOf(root, '[data-area=status-bar]').includes('version 4'));
  await viewer.selectStep('step.write');
  assert.equal(fieldValue(root, 'toolbox_id'), 't4');
});

test('TC-GA-018 REQ-GA-020: the filter keeps the graphs whose ID or description holds every typed word, ignoring case', async () => {
  // Example: "chat" -> chat; "CODE step" -> sample.code (its description holds "code step"); "" and "   " -> all four.
  // Given the list of cp2.multi, sample.code, sample.broken and chat ("Chat with the owner")
  const mock = await seededMock(['cp2.multi', 'sample.code', 'sample.broken', 'chat']);
  const { root, viewer } = await pageWith({ mock });
  await viewer.start();
  const all = ['chat', 'cp2.multi', 'sample.broken', 'sample.code'];
  // When the owner types chat, CODE step, nothing and three spaces
  viewer.filter('chat');
  const chat = listed(root);
  viewer.filter('CODE step');
  const codeStep = listed(root);
  viewer.filter('');
  const none = listed(root);
  viewer.filter('   ');
  const spaces = listed(root);
  // Then chat keeps exactly chat and CODE step keeps exactly sample.code
  assert.deepEqual(chat, ['chat']);
  assert.deepEqual(codeStep, ['sample.code']);
  // And nothing and spaces keep all four
  assert.deepEqual([...none].sort(), all);
  assert.deepEqual([...spaces].sort(), all);
});

test('TC-GA-019 REQ-GA-022: not logged in shows no list and no picture, and a link to the main app\'s login', async () => {
  // Example: every route 401 unauthenticated -> no [data-graph-id], no drawing, [data-login] with a[href="/"].
  // Given the JS mock with graphs but no session
  const mock = await seededMock(['cp2.multi'], { login: false });
  const { root, viewer, drawing } = await pageWith({ mock });
  // When the page loads
  await viewer.start();
  // Then no list and no picture are shown
  assert.deepEqual(listed(root), []);
  assert.equal(drawing.shows.length, 0);
  // And the page shows a link to the main app's login
  const note = root.querySelector('[data-login]');
  assert.ok(note, 'no [data-login] note');
  assert.ok(note.querySelector('a[href="/"]'), 'no link to the main app');
});

test('TC-GA-020 REQ-GA-023: a store that stops answering keeps the picture and the list, and says so', async () => {
  // Example: cp2.multi drawn, then 503 store_unreachable on the list and the graph -> same picture, one notice line.
  // Given cp2.multi opened from the JS mock
  const mock = await seededMock(['cp2.multi']);
  const { root, viewer, drawing } = await pageWith({ mock });
  await viewer.start();
  await viewer.open('cp2.multi');
  const drawn = drawing.last().data.nodes.map((n) => n.id);
  // When the store stops answering, the list is loaded again and cp2.multi chosen again
  mock.unreachable = true;
  await viewer.start();
  await viewer.open('cp2.multi');
  // Then the picture of version 4 is still shown, and the list still holds cp2.multi
  assert.deepEqual(drawing.last().data.nodes.map((n) => n.id), drawn);
  assert.ok(textOf(root, '[data-area=status-bar]').includes('version 4'));
  assert.deepEqual(listed(root), ['cp2.multi']);
  // And one line says that the store does not answer
  assert.equal(root.querySelectorAll('[data-notice=store_unreachable]').length, 1);
  assert.ok(textOf(root, '[data-notice=store_unreachable]').trim().length > 0);
});

test('TC-GA-021 REQ-GA-017 REQ-GA-018: the status bar names graph, version, author, time and read-only; the store entry is text only', async () => {
  // Example: cp2.multi version 4 by ben at the time the mock gives it; the store entry reads files and reachable, without a control.
  // Given cp2.multi at version 4 by ben; the store route answering files, reachable
  const mock = await seededMock(['cp2.multi']);
  const time = (await mockGet(mock, '/api/v2/graphs/cp2.multi/versions')).at(-1).time;
  const { root, viewer } = await pageWith({ mock });
  // When cp2.multi is opened and other things is read
  await viewer.start();
  await viewer.open('cp2.multi');
  // Then the status bar shows the ID, version 4, ben, the time of version 4 and read-only
  const status = textOf(root, '[data-area=status-bar]');
  for (const part of ['cp2.multi', 'version 4', 'ben', time, 'read-only']) assert.ok(status.includes(part), `${part} in ${status}`);
  // And other things shows files and reachable as text, with no control
  const store = root.querySelector('[data-area=other-things] [data-store]');
  assert.ok(store, 'no [data-store] in other things');
  assert.ok(store.textContent.includes('files'));
  assert.ok(store.textContent.includes('reachable') && !store.textContent.includes('not reachable'));
  assert.equal(store.querySelectorAll(CONTROLS).length, 0);
});

test('TC-GA-022 REQ-GA-024: every step and every connection is drawn, each connection with its direction', async () => {
  // Example: sample.code -> 7 nodes with the stored IDs, 6 edges e1..e6 between the stored ends, each with arrows 'to'.
  // Given sample.code in the JS mock (7 steps, 6 connections)
  const mock = await seededMock(['sample.code']);
  const stored = (await mockGet(mock, '/api/v2/graphs/sample.code')).graph;
  const { viewer, drawing } = await pageWith({ mock });
  // When it is opened
  await viewer.start();
  await viewer.open('sample.code');
  // Then the drawing holds the 7 stored steps and the 6 stored connections between their stored ends
  const { nodes, edges } = drawing.last().data;
  assert.deepEqual(nodes.map((n) => n.id).sort(), stored.nodes.map((n) => n.id).sort());
  assert.deepEqual(edges.map((e) => [e.id, e.from, e.to]).sort(), stored.edges.map((e) => [e.id, e.from, e.to]).sort());
  assert.equal(nodes.length, 7);
  assert.equal(edges.length, 6);
  // And every connection has an arrow at its end step
  assert.ok(edges.every((e) => e.arrows === 'to'));
});

test('TC-GA-023 REQ-GA-025: a connection to a missing step is drawn dashed to a marked missing step and named in the left column', async () => {
  // Example: sample.broken e2 -> var.gone: node var.gone {missing: true, kind: 'missing step'}, e2 dashes true, e1 not; [data-problem] names e2 and var.gone.
  // Given sample.broken (e2 from step.a to the missing var.gone)
  const mock = await seededMock(['sample.broken']);
  const { root, viewer, drawing } = await pageWith({ mock });
  // When it is opened
  await viewer.start();
  await viewer.open('sample.broken');
  const { nodes, edges } = drawing.last().data;
  const node = (id) => nodes.find((n) => n.id === id);
  const edge = (id) => edges.find((e) => e.id === id);
  // Then e2 is dashed to a step var.gone marked as missing
  assert.ok(node('var.gone'), 'no node for the missing step');
  assert.equal(node('var.gone').missing, true);
  assert.equal(node('var.gone').kind, 'missing step');
  assert.equal(edge('e2').to, 'var.gone');
  assert.equal(edge('e2').dashes, true);
  // And var.in, step.a and e1 are drawn as usual
  assert.ok(!node('var.in').missing && !node('step.a').missing);
  assert.ok(!edge('e1').dashes);
  // And the left column names the problem
  const problem = textOf(root, '[data-area=left-column] [data-problem]');
  assert.ok(problem.includes('e2') && problem.includes('var.gone'), problem);
});

test('TC-GA-024 REQ-GA-026 REQ-GA-027: kinds differ by shape and word; marks only where attention is needed', async () => {
  // Example: var.in ellipse "data", step.check box "processing", loop.review hexagon "loop-controlling"; only the hostile step has marks: untrusted, code.
  // Given sample.code; the hostile step untrusted and holding code, step.check and loop.review trusted
  const mock = await seededMock(['sample.code']);
  const { viewer, drawing } = await pageWith({ mock });
  // When it is opened
  await viewer.start();
  await viewer.open('sample.code');
  const node = (id) => drawing.last().data.nodes.find((n) => n.id === id);
  // Then the three kinds have their shape and their word
  assert.deepEqual([node('var.in').shape, node('var.in').kind], ['ellipse', 'data']);
  assert.deepEqual([node('step.check').shape, node('step.check').kind], ['box', 'processing']);
  assert.deepEqual([node('loop.review').shape, node('loop.review').kind], ['hexagon', 'loop-controlling']);
  // And the hostile step carries untrusted and code, each one word; no other step carries a mark
  assert.deepEqual([...node(HOSTILE).marks].sort(), ['code', 'untrusted']);
  assert.ok(node(HOSTILE).marks.every((m) => /^\S+$/.test(m)));
  for (const n of drawing.last().data.nodes) if (n.id !== HOSTILE) assert.deepEqual(n.marks ?? [], [], n.id);
});

test('TC-GA-025 REQ-GA-028: a graph of another kind is drawn in one neutral shape with its type in words, no marks', async () => {
  // Example: ctx.small -> boxes "concept", "source"; swarm.one -> boxes "agent", its untrusted step unmarked; the status bar names the kind.
  // Given a context graph and a graph of kind swarm with an untrusted step
  const mock = await seededMock(['ctx.small', 'swarm.one']);
  const { root, viewer, drawing } = await pageWith({ mock });
  await viewer.start();
  for (const [id, kind, types] of [['ctx.small', 'context', ['concept', 'source']], ['swarm.one', 'swarm', ['agent']]]) {
    // When each is opened
    await viewer.open(id);
    const { nodes } = drawing.last().data;
    // Then every step is a box labelled with its type, and no step carries a mark
    assert.ok(nodes.every((n) => n.shape === 'box'), id);
    assert.deepEqual([...new Set(nodes.map((n) => n.kind))].sort(), types);
    assert.ok(nodes.every((n) => (n.marks ?? []).length === 0), id);
    // And the status bar names the kind, and the page offers no control that changes the graph
    assert.ok(textOf(root, '[data-area=status-bar]').includes(kind), kind);
    const writers = root.querySelectorAll('button').filter((b) => /save|delete|edit|restore|keep|change/i.test(b.textContent));
    assert.deepEqual(writers.map((b) => b.textContent), []);
  }
});

test('TC-GA-026 REQ-GA-030: a saved arrangement places its steps; the others are left to the solver', async () => {
  // Example: arrangement var.in at 10, -3 -> node var.in {x: 10, y: -3, fixed: true}; step.write without a place.
  // Given cp2.multi with the saved arrangement var.in at 10, -3 (saved by anna, the owner)
  const mock = await seededMock(['cp2.multi']);
  const saved = await mock.fetch('/api/v2/graphs/cp2.multi/arrangement', { method: 'PUT', body: JSON.stringify({ positions: { 'var.in': { x: 10, y: -3 } } }), headers: { Origin: mock.origin } });
  assert.equal(saved.status, 200);
  const { viewer, drawing } = await pageWith({ mock });
  // When it is opened
  await viewer.start();
  await viewer.open('cp2.multi');
  const node = (id) => drawing.last().data.nodes.find((n) => n.id === id);
  // Then var.in is placed at 10, -3 and held there
  assert.deepEqual([node('var.in').x, node('var.in').y], [10, -3]);
  assert.ok(node('var.in').fixed);
  // And step.write and var.out are placed by the solver
  for (const id of ['step.write', 'var.out']) assert.ok(node(id).x === undefined && !node(id).fixed, id);
});

test('TC-GA-027 REQ-GA-033: the layered reset points every connection forward', async () => {
  // Example: after layered(), every edge of sample.code goes from a node of a lower level to a node of a higher level.
  // Given sample.code opened
  const mock = await seededMock(['sample.code']);
  const { viewer, drawing } = await pageWith({ mock });
  await viewer.start();
  await viewer.open('sample.code');
  // When the owner asks for the layered arrangement
  await viewer.layered();
  // Then each of e1 to e6 goes from a lower layer to a higher layer
  const { nodes, edges } = drawing.last().data;
  const level = Object.fromEntries(nodes.map((n) => [n.id, n.level]));
  assert.ok(nodes.every((n) => Number.isInteger(n.level)), 'every node needs a level');
  for (const e of edges) assert.ok(level[e.from] < level[e.to], `${e.id}: ${level[e.from]} -> ${level[e.to]}`);
  assert.equal(edges.length, 6);
});

test('TC-GA-028 REQ-GA-034 REQ-GA-035: settings change the picture at once, are remembered, and fall back to defaults', async () => {
  // Example: straight + off -> options {edges: 'straight', physics: false}, no new read, step.check stays at 500, 400; a fresh page starts straight and off; a blocked storage starts rounded and on.
  // Given sample.code opened, step.check moved, an in-memory storage
  const mock = await seededMock(['sample.code']);
  const storage = memoryStorage();
  const first = await pageWith({ mock, storage });
  await first.viewer.start();
  await first.viewer.open('sample.code');
  first.drawing.drag('step.check', 500, 400);
  const reads = gets(mock, '/api/v2/graphs/sample.code');
  // When the owner switches to straight connections and the arrangement off
  await first.viewer.setSettings({ edges: 'straight', arrangement: 'off' });
  // Then the drawing options change at once, the graph is not read again, and step.check keeps its place
  assert.equal(first.drawing.current().edges, 'straight');
  assert.equal(first.drawing.current().physics, false);
  assert.equal(gets(mock, '/api/v2/graphs/sample.code'), reads);
  assert.deepEqual(first.drawing.places['step.check'], { x: 500, y: 400 });
  // And a fresh page with the same storage starts with straight and off
  const second = await pageWith({ mock, storage });
  await second.viewer.start();
  await second.viewer.open('sample.code');
  assert.deepEqual([second.drawing.current().edges, second.drawing.current().physics], ['straight', false]);
  // And a page whose storage throws starts with rounded and on, and works
  const third = await pageWith({ mock, storage: throwingStorage() });
  await third.viewer.start();
  await third.viewer.open('sample.code');
  assert.deepEqual([third.drawing.current().edges, third.drawing.current().physics], ['rounded', true]);
  assert.equal(third.drawing.last().data.nodes.length, 7);
});

test('TC-GA-029 REQ-GA-036 REQ-GA-044 REQ-GA-037: the left column shows the selection, trust in words, and empties on nothing', async () => {
  // Example: step.check -> kind processing, toolbox_id check.number; hostile -> trust untrusted, lifecycle none, reason "it is not in the toolbox", changed no, code yes.
  // Given sample.code opened
  const mock = await seededMock(['sample.code']);
  const { root, viewer } = await pageWith({ mock });
  await viewer.start();
  await viewer.open('sample.code');
  const column = () => root.querySelector('[data-area=left-column]');
  // When the owner selects step.check
  await viewer.selectStep('step.check');
  // Then the column shows its kind and toolbox ID as fields and its full stored text
  assert.equal(fieldValue(column(), 'kind'), 'processing');
  assert.equal(fieldValue(column(), 'toolbox_id'), 'check.number');
  assert.ok(textOf(column(), '[data-stored-text]').includes('"check.number"'));
  // And for the hostile step trust, lifecycle, reason, changed since trusted and code in words
  await viewer.selectStep(HOSTILE);
  assert.deepEqual(['trust', 'lifecycle', 'reason', 'changed_since_trusted', 'code'].map((f) => fieldValue(column(), f)),
    ['untrusted', 'none', 'it is not in the toolbox', 'no', 'yes']);
  // And for e2 its ends and role and its stored text
  await viewer.selectConnection('e2');
  assert.deepEqual(['from', 'to', 'role'].map((f) => fieldValue(column(), f)), ['var.code', HOSTILE, 'code']);
  assert.ok(textOf(column(), '[data-stored-text]').includes('"role": "code"'));
  // And after selecting nothing the column holds no field and no stored text
  await viewer.selectNothing();
  assert.equal(column().querySelectorAll('[data-field]').length, 0);
  assert.equal(column().querySelectorAll('[data-stored-text]').length, 0);
});

test('TC-GA-030 REQ-GA-038 REQ-GA-039 REQ-GA-040: history newest first, an earlier version read-only, previous and next', async () => {
  // Example: cp2.multi -> 4 ben, 3 anna, 2 ben, 1 anna, 4 current; version 2 names t2; from 1 no previous; at 4 no next; sample.code offers neither.
  // Given cp2.multi with versions 1 to 4 by anna, ben, anna, ben, and sample.code with one version
  const mock = await seededMock(['cp2.multi', 'sample.code']);
  const times = Object.fromEntries((await mockGet(mock, '/api/v2/graphs/cp2.multi/versions')).map((v) => [v.version, v.time]));
  const { root, viewer } = await pageWith({ mock });
  await viewer.start();
  await viewer.open('cp2.multi');
  const status = () => textOf(root, '[data-area=status-bar]');
  // When the owner opens the history
  await viewer.openHistory();
  // Then it lists 4, 3, 2, 1 with who and when, 4 marked current
  const entries = root.querySelectorAll('[data-version]');
  assert.deepEqual(entries.map((e) => e.dataset.version), ['4', '3', '2', '1']);
  ['ben', 'anna', 'ben', 'anna'].forEach((who, i) => assert.ok(entries[i].textContent.includes(who) && entries[i].textContent.includes(times[4 - i]), entries[i].textContent));
  assert.deepEqual(entries.map((e) => e.dataset.current === 'true'), [true, false, false, false]);
  // When version 2 is chosen
  await viewer.showVersion(2);
  // Then it is drawn read-only (t2) and the status bar names version 2 and its time
  await viewer.selectStep('step.write');
  assert.equal(fieldValue(root, 'toolbox_id'), 't2');
  assert.ok(status().includes('version 2') && status().includes(times[2]) && status().includes('read-only'), status());
  // When previous is pressed, then next twice
  await viewer.previous();
  assert.ok(status().includes('version 1'));
  assert.equal(offered(root, '#history-previous'), false);
  await viewer.next();
  assert.ok(status().includes('version 2'));
  await viewer.next();
  assert.ok(status().includes('version 3'));
  await viewer.next();
  // Then at 4 no next is offered
  assert.ok(status().includes('version 4'));
  assert.equal(offered(root, '#history-next'), false);
  // And a graph of one version offers neither previous nor next
  await viewer.open('sample.code');
  await viewer.openHistory();
  assert.deepEqual([offered(root, '#history-previous'), offered(root, '#history-next')], [false, false]);
});

test('helper: the JS mock still answers 401 without a session (the stand-in of TC-GA-019 fires)', async () => {
  // TR-VIEW-006: the fault stand-ins are shown to fire. A mock without a login refuses the list; the unreachable mock refuses it with 503.
  const bare = new GraphApiV2Mock();
  assert.equal((await bare.fetch('/api/v2/graphs')).status, 401);
  const mock = await seededMock(['cp2.multi']);
  mock.unreachable = true;
  assert.equal((await mock.fetch('/api/v2/graphs')).status, 503);
});
