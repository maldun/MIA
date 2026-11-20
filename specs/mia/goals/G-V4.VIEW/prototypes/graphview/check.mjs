// PROTOTYPE check (own test, not a protected check): every stored graph read over HTTP gives a drawing with all its nodes and edges.
import { visData } from '../../../../../../graph_app/graph-view.js';
import { toViewGraph } from './adapter.js';
const base = process.argv[2];
const ids = await (await fetch(`${base}/proto/graphs`)).json();
let ok = 0, bad = [];
for (const id of ids) {
  const g = await (await fetch(`${base}/proto/graphs/${encodeURIComponent(id)}`)).json();
  const d = visData(toViewGraph(g));
  const kinds = new Set(d.nodes.map((n) => n.group));
  if (d.nodes.length === g.nodes.length && d.edges.length === g.edges.length && !d.problems.length && kinds.has('process')) ok += 1; else bad.push(id);
}
console.log(`graphs ${ids.length}, drawn completely ${ok}`, bad.length ? 'FAILED ' + bad : '');
process.exit(bad.length ? 1 : 0);
