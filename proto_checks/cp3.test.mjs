// PROTOTYPE CP3 checks (node --test): what the owner is told about the sync (FR-93)
import test from 'node:test';
import assert from 'node:assert/strict';
import { storeNote, syncMessage } from '../graph_app_v2/store-note.js';

test('FR-93: the header names the graphs that differ on the copy and says what the next sync does', () => {
  const note = storeNote({ split: true, live: 'reachable', lag: 0, differs: { 'sample.code': 'conflict' } });
  assert.match(note, /copy is up to date/);
  assert.match(note, /1 graph\(s\) differ on the copy \(sample.code\).*live store wins.*set aside, named/);
  assert.doesNotMatch(storeNote({ split: true, live: 'reachable', lag: 0, differs: {} }), /differ/);
  assert.match(storeNote({ split: true, live: 'reachable', lag: 2, differs: {} }), /behind by 2/);
});

test('FR-93: after a sync the owner is told what was added and, if anything, which versions were set aside and where', () => {
  assert.equal(syncMessage({ records: 3, set_aside: {} }), 'Synced: 3 record(s) added to the copy.');
  assert.equal(syncMessage({ records: 0 }), 'Synced: 0 record(s) added to the copy.');
  const m = syncMessage({ records: 1, set_aside: { 'sample.code': { versions: [2, 3], file: '/x/a.json' } } });
  assert.match(m, /Set aside, because the live store wins: sample.code \(version 2, 3\) in \/x\/a.json/);
});
