// The store entry and the status line of the graph viewer (graph_app/store-note.js, REQ-GA-017, REQ-GA-018). Run: node --test tests/js/store-note.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { storeEntry, graphStatus } from '../../graph_app/store-note.js';

test('REQ-GA-018: the store entry names the store and whether it answers', () => {
  // Example: files reachable -> "files, reachable"; database down -> "database, not reachable"; a copy shown is named.
  // Given three answers of the store route
  const answers = [{ store: 'files', reachable: true, shown: 'live' }, { store: 'database', reachable: false, shown: 'live' },
    { store: 'database', reachable: true, shown: 'copy' }];
  // When each is put into words
  const lines = answers.map(storeEntry);
  // Then each names the store and whether it answers
  assert.deepEqual(lines, ['files, reachable', 'database, not reachable', 'database, reachable; showing the copy']);
});

test('REQ-GA-017: the status line names graph, kind, version, author, time and read-only', () => {
  // Example: cp2.multi version 4 of 4 by ben -> "cp2.multi · workflow · version 4 · stored by ben · <time> · read-only"; version 2 of 4 names both.
  // Given the current and an older version as the read route answers them
  const graph = { id: 'cp2.multi', nodes: [], edges: [] };
  const current = { graph, version: 4, current: 4, author: 'ben', time: '2026-11-20T12:00:04Z' };
  const older = { graph: { ...graph, kind: 'context' }, version: 2, current: 4, author: 'anna', time: '2026-11-20T12:00:02Z' };
  // When each is put into words
  // Then the line holds every part, the older one with the newest version too
  assert.equal(graphStatus(current), 'cp2.multi · workflow · version 4 · stored by ben · 2026-11-20T12:00:04Z · read-only');
  assert.equal(graphStatus(older), 'cp2.multi · context · version 2 of 4 · stored by anna · 2026-11-20T12:00:02Z · read-only');
});
