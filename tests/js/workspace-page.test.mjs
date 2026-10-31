// The page wiring of the workspace dialog (workspace.js, N-1.1) on a fake DOM, a fake socket and a fake REST client: F2 and F6 of the verification report.
// Markers: `// mark.req(...)` above a test (trace_check reads Python markers only).  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { installDocument, fakeSocket, flush } from './fake-dom.mjs';
import { initWorkspace } from '../../templates/static/chat/workspace.js';
import { dueToField } from '../../templates/static/chat/panels-model.js';

const t = (key) => key;

/** the workspace on fakes; `records` are the lists of the REST client per kind, `files` its file list; every call is kept in `calls` */
function page({ records = {}, files = [] } = {}) {
  const doc = installDocument();
  const make = (tag) => doc.createElement(tag);
  const els = { dialog: make('dialog'), tabsEl: make('div'), body: make('div'), closeButton: make('button') };
  const calls = [];
  const api = {
    items: async (kind) => { calls.push(['items', kind]); return records[kind] ?? []; },
    saveItem: async (...args) => { calls.push(['saveItem', ...args]); return {}; },
    deleteItem: async (...args) => { calls.push(['deleteItem', ...args]); return { deleted: true }; },
    files: async () => { calls.push(['files']); return files; },
    trust: async () => ({}),
    persona: async () => { calls.push(['persona']); return { text: 'calm' }; },
    score: async () => ({ overall: 0, categories: {} }),
  };
  const socket = fakeSocket();
  const notes = [];
  const workspace = initWorkspace({ ...els, api, socket, t, notify: (n) => notes.push(n) });
  const rows = () => els.body.querySelectorAll('.workspace-list li');
  const button = (row, label) => row.querySelectorAll('button').find((b) => b.textContent === label);
  return { ...els, api, socket, notes, calls, workspace, rows, button };
}

const task = { id: 't1', text: 'water the plants', author: 'anna', created: '2026-10-31T10:00:00Z', due: '2026-11-02T08:00:30Z' };

// --- F2: the due time of a task (REQ-CLV-011, REQ-CHA-019, D-163) --------------------------------------------------
// mark.req("REQ-CLV-011", "REQ-CHA-019")
test('F2: an edit of the text of a task keeps its due time exactly as it was', async () => {
  // Given: the Tasks tab with a task that is due
  const p = page({ records: { tasks: [task] } });
  await p.workspace.open('tasks');
  const row = p.rows()[0];
  // When: the text is changed and saved, the due field untouched
  row.querySelector('input.item-text').value = 'water the plants and the herbs';
  p.button(row, 'workspace.save').click();
  await flush();
  // Then: the save carries the same due time, seconds included (a new due time would make MIA say the task again)
  assert.deepEqual(p.calls.find((c) => c[0] === 'saveItem'), ['saveItem', 'tasks', 't1', 'water the plants and the herbs', null, '2026-11-02T08:00:30Z']);
});

// mark.req("REQ-CLV-011", "REQ-CHA-019")
test('F2: the Tasks tab shows the due time of a task in a field, and an emptied field clears it', async () => {
  // Given: the Tasks tab with a task that is due
  const p = page({ records: { tasks: [task] } });
  await p.workspace.open('tasks');
  const row = p.rows()[0];
  const due = row.querySelector('input.item-due');
  // Then: the field shows the due time in local time
  assert.equal(due.type, 'datetime-local');
  assert.equal(due.value, dueToField(task.due));
  // When: the field is emptied and the task saved
  due.value = '';
  p.button(row, 'workspace.save').click();
  await flush();
  // Then: the save has no due time
  assert.equal(p.calls.find((c) => c[0] === 'saveItem')[5], null);
});

// mark.req("REQ-CLV-011", "REQ-CHA-019")
test('F2: a new task can get a due time; memos and memory have no due field', async () => {
  // Given: the Tasks tab, empty
  const p = page();
  await p.workspace.open('tasks');
  const form = p.body.querySelector('form.workspace-add');
  // When: a new task with a due time is added
  form.querySelector('input.item-text').value = 'call the plumber';
  form.querySelector('input.item-due').value = dueToField('2026-11-03T15:00:00Z');
  form.requestSubmit();
  await flush();
  // Then: it is saved with that due time in UTC
  assert.deepEqual(p.calls.find((c) => c[0] === 'saveItem'), ['saveItem', 'tasks', null, 'call the plumber', null, '2026-11-03T15:00:00Z']);
  // When: the memos tab is opened
  await p.workspace.open('memos');
  // Then: it has no due field
  assert.equal(p.body.querySelector('input.item-due'), null);
});

// --- F6: what the tabs draw and when they are drawn again ----------------------------------------------------------
const report = { name: 'review 2026-10-31.pdf', size: 2048, created: '2026-10-31T11:00:00Z', task: 'review' };

// mark.req("REQ-CLV-024")
test('TC-CLV-024: the Files tab lists each file with a download link and offers no delete (F6)', async () => {
  // Given: the server lists one file
  const p = page({ files: [report] });
  // When: the Files tab is opened
  await p.workspace.open('files');
  // Then: one row with a link to /api/files/<name> that downloads it, and no button
  const rows = p.rows();
  assert.equal(rows.length, 1);
  const link = rows[0].querySelector('a');
  assert.equal(link.href, '/api/files/review%202026-10-31.pdf');
  assert.equal(link.download, report.name);
  assert.equal(p.body.querySelectorAll('button').length, 0);
});

// mark.req("REQ-CLV-024")
test('TC-CLV-024: files_changed draws the open Files tab again (F6)', async () => {
  // Given: the open Files tab, listed once
  const p = page({ files: [report] });
  await p.workspace.open('files');
  p.dialog.showModal();
  // When: a task stores a new file
  p.socket.fire('files_changed', { name: 'b.pdf', task: 'review' });
  await flush();
  // Then: the list is asked again
  assert.equal(p.calls.filter((c) => c[0] === 'files').length, 2);
});

// mark.req("REQ-CLV-009")
test('TC-CLV-009: a persona change of another user draws the open Persona tab again, but not while the reader types in it (F6)', async () => {
  // Given: the open Persona tab
  const p = page();
  await p.workspace.open('persona');
  // When: another user changes the persona
  p.socket.fire('persona_changed', { author: 'ben' });
  await flush();
  // Then: the persona is read again
  assert.equal(p.calls.filter((c) => c[0] === 'persona').length, 2);
  // When: the reader types in the text and another change arrives
  p.body.querySelector('textarea').focus();
  p.socket.fire('persona_changed', { author: 'ben' });
  await flush();
  // Then: nothing is overwritten, a note says why
  assert.equal(p.calls.filter((c) => c[0] === 'persona').length, 2);
  assert.deepEqual(p.notes, ['workspace.changed_elsewhere']);
});

// mark.req("REQ-CLV-011")
test('TC-CLV-011: item_changed draws the open tab of that kind again, another kind does not (F6)', async () => {
  // Given: the open Tasks tab
  const p = page({ records: { tasks: [task] } });
  await p.workspace.open('tasks');
  // When: a memo and then a task change elsewhere
  p.socket.fire('item_changed', { kind: 'memos', id: 'm1', author: 'ben', deleted: false });
  await flush();
  p.socket.fire('item_changed', { kind: 'tasks', id: 't1', author: 'ben', deleted: true });
  await flush();
  // Then: the tasks are read once more, the memos never
  assert.deepEqual(p.calls.filter((c) => c[0] === 'items').map((c) => c[1]), ['tasks', 'tasks']);
});
