// PROTOTYPE CP5: what cannot be drawn is marked on the drawing (FR-49): a connection to a step that does not exist ends in a marked "missing step".
import { toViewGraph } from './adapter.js';

/** the graph as the viewer draws it: the stored steps, plus a marked placeholder for every missing step; the problems are named in `named` */
export function withProblemMarks(graph, problems) {
  const view = toViewGraph(graph);
  const missing = [...new Set(problems.filter((p) => p.problem === 'missing_step').map((p) => p.step))];
  for (const id of missing) view.nodes.push({ id, kind: 'missing', data: { type: 'missing' }, missing: true });
  const named = problems.map((p) => (p.problem === 'missing_step' ? `connection ${p.connection}: the ${p.end === 'to' ? 'target' : 'source'} step "${p.step}" does not exist` : `step ${p.step}: the id is used twice`));
  return { graph: view, named, missing: new Set(missing) };
}
