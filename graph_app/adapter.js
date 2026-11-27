// The picture of a stored graph as the drawing gets it (R6, written again for REQ-GA-024 to 028; page-interface-note.md section 3). Pure.
import { isWorkflow, kindOf, marksOf } from './step-marks.js';
import { missingSteps } from './problems.js';

/** {nodes, edges} for the drawing: every stored step and connection (REQ-GA-024), a marked missing step for each end that is not there,
 *  its connections dashed (REQ-GA-025); labels are plain text (REQ-GA-029) */
export function pictureOf({ graph, steps = {}, problems = [] }) {
  const workflow = isWorkflow(graph);
  const missing = missingSteps(problems);
  const once = graph.nodes.filter((n, i) => graph.nodes.findIndex((m) => m.id === n.id) === i);      // a step ID used twice is drawn once; the problem names it
  const nodes = once.map((n) => {
    const { shape, kind } = kindOf(n, workflow);
    const marks = workflow ? marksOf(steps[n.id]) : [];
    return { id: n.id, label: labelOf(n.id, kind, marks), shape, kind, marks, missing: false };
  });
  for (const id of missing) nodes.push({ id, label: labelOf(id, 'missing step', []), shape: 'box', kind: 'missing step', marks: [], missing: true });
  const gone = new Set(missing);
  const edges = graph.edges.map((e) => ({ id: e.id, from: e.from, to: e.to, arrows: 'to', dashes: gone.has(e.from) || gone.has(e.to) }));
  return { nodes, edges };
}

/** the text on a step: its ID, then its kind in words and its marks */
export function labelOf(id, kind, marks) {
  return `${id}\n${[kind, ...marks].join(' · ')}`;
}
