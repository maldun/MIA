// The pure parts of the Report part of the Full run (G-V3.REPORT T-04, REQ-CLV-048, 050, 051): what the part shows from a run record, and how the page reads a report file.
// The page itself is checked in the browser (TC-CLV-048, 050, 051, 052).
import test from 'node:test';
import assert from 'node:assert/strict';
import { reportModel } from '../../templates/static/chat/skill-run-model.js';
import { createApi, ApiError } from '../../templates/static/chat/api.js';

test('REQ-CLV-050: a record that names no report is waiting, one that names it is ready', () => {
  // Example: a running run has report null: waiting; the ended run names "lookup-2026-11-08-canary.md": ready
  // Given: records before and after the end of a run, a status without the field, and nothing
  // When / Then: the model says what the part shows
  assert.deepEqual(reportModel({ id: 'r1', state: 'running', report: null }), { state: 'running', name: null, kind: 'waiting' });
  assert.deepEqual(reportModel({ id: 'r1', state: 'done', report: 'lookup-2026-11-08-canary.md' }), { state: 'done', name: 'lookup-2026-11-08-canary.md', kind: 'ready' });
  assert.deepEqual(reportModel({ id: 'r1', state: 'running' }), { state: 'running', name: null, kind: 'waiting' });
  assert.deepEqual(reportModel(null), { state: '', name: null, kind: 'waiting' });
  assert.equal(reportModel({ id: 'r1', state: 'done', report: '' }).kind, 'waiting');
});

const respond = (status, body) => async () => ({ status, ok: status >= 200 && status < 300, text: async () => body, json: async () => ({}) });

test('REQ-CLV-048: the page reads the report file as text from /api/files/<name>', async () => {
  // Example: "report one.md" is asked for as /api/files/report%20one.md and its text comes back as it is
  // Given: a files volume that answers with the text
  const asked = [];
  const api = createApi({ origin: 'http://mia.test', fetchFn: async (url, init) => { asked.push([String(url), init.credentials]); return respond(200, '# Done\n')(); } });
  // When: the report is read
  const text = await api.reportText('report one.md');
  // Then: the address is the encoded file address, the session goes along and the text is unchanged
  assert.deepEqual(asked, [['http://mia.test/api/files/report%20one.md', 'same-origin']]);
  assert.equal(text, '# Done\n');
});

test('REQ-CLV-051: a report file that is gone (404) is null, any other failure is an error', async () => {
  // Example: 404 means "the file was removed"; 500 and a lost connection are errors, not a removed file
  // Given / When / Then: each answer of the volume
  assert.equal(await createApi({ origin: 'http://mia.test', fetchFn: respond(404, '') }).reportText('x.md'), null);
  await assert.rejects(createApi({ origin: 'http://mia.test', fetchFn: respond(500, '') }).reportText('x.md'), (error) => error instanceof ApiError && error.status === 500);
  await assert.rejects(createApi({ origin: 'http://mia.test', fetchFn: async () => { throw new Error('down'); } }).reportText('x.md'), (error) => error instanceof ApiError && error.status === 0);
});
