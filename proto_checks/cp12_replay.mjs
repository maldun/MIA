// PROTOTYPE CP12 helper: replays the recorded entries of a dumped graph with the page's own code and compares with the saved versions.
// usage: node proto_checks/cp12_replay.mjs <dump.json>   dump: {versions: {n: graph}, records: [{version, from_version, kind, entries}]}
import fs from 'node:fs';
import { states, sameGraph } from '../graph_app_v2/replay.js';
import { compareView } from '../graph_app_v2/compare.js';
const dump = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = { replay: [], compare: [] };
for (const r of dump.records.filter((x) => x.kind !== 'before_the_record')) {
  const list = states(dump.versions[r.from_version], r.entries, (n) => dump.versions[n]);
  out.replay.push({ version: r.version, ok: sameGraph(list.at(-1), dump.versions[r.version]), steps: list.length - 1 });
}
const ns = Object.keys(dump.versions).map(Number);
for (const a of ns) for (const b of ns) if (a < b) { const v = compareView(dump.versions[a], dump.versions[b]); out.compare.push({ a, b, lines: v.lines.length, none: v.none, marks: Object.keys(v.marks).length + Object.keys(v.edgeMarks).length }); }
console.log(JSON.stringify(out));
