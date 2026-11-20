// PROTOTYPE CP12 (G-V4.REPLAY, FR-79): what differs between two versions of a graph, as a list and as marks on one drawing. Pure.
import { diffChanges, describeChange } from './change-log.js';

const same = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);

/** {graph, marks, edgeMarks, lines, none}: `graph` holds every step and connection of both versions (so a removed one can be drawn), `marks` maps a step ID and `edgeMarks` a connection ID to
 *  added | removed | changed; `lines` lists each difference with its old and new content */
export function compareView(a, b) {
  const an = new Map(a.nodes.map((n) => [n.id, n])), bn = new Map(b.nodes.map((n) => [n.id, n]));
  const ae = new Map(a.edges.map((e) => [e.id, e])), be = new Map(b.edges.map((e) => [e.id, e]));
  const marks = {}, edgeMarks = {};
  for (const [id, n] of bn) marks[id] = !an.has(id) ? 'added' : same(an.get(id).data, n.data) ? undefined : 'changed';
  for (const id of an.keys()) if (!bn.has(id)) marks[id] = 'removed';
  for (const [id, e] of be) edgeMarks[id] = !ae.has(id) ? 'added' : same([ae.get(id).from, ae.get(id).to, ae.get(id).data], [e.from, e.to, e.data]) ? undefined : 'changed';
  for (const [id, e] of ae) if (!be.has(id)) edgeMarks[id] = 'removed';
  for (const k of Object.keys(marks)) if (!marks[k]) delete marks[k];
  for (const k of Object.keys(edgeMarks)) if (!edgeMarks[k]) delete edgeMarks[k];
  const nodes = [...bn.values(), ...[...an.values()].filter((n) => !bn.has(n.id))];
  const edges = [...be.values(), ...[...ae.values()].filter((e) => !be.has(e.id))];
  const lines = diffChanges(a, b).map(describeChange);
  return { graph: { nodes, edges }, marks, edgeMarks, lines, none: lines.length === 0 };
}

/** the text added to a step's name for a mark, so the mark does not rest on colour alone */
export const markText = (mark) => (mark ? `[${mark}]` : '');

/** the line above the comparison */
export const compareNote = (from, to, view) => (view.none ? `Version ${from} and version ${to} have the same steps and connections.` : `Version ${from} compared with version ${to}: ${view.lines.length} difference(s). Marked on the drawing: added, removed, changed.`);
