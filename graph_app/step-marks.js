// The kind of a step and its marks at a glance (R6, written again for REQ-GA-026 to 028 and D-426). Pure: strings in, strings out, so it
// is tested without a browser and nothing here can become markup.

/** the shape and the word of each kind of a workflow step: the kinds differ by shape and by word, never by colour alone (REQ-GA-026) */
const WORKFLOW = { data: ['ellipse', 'data'], transform: ['box', 'processing'], master: ['hexagon', 'loop-controlling'] };

/** whether a graph is drawn with the workflow shapes; any other kind is drawn neutrally (REQ-GA-028) */
export const isWorkflow = (graph) => (graph.kind ?? 'workflow') === 'workflow';

/** {shape, kind} of a stored step; a step of another graph kind, or of an unknown type, is a box with its stored type in words */
export function kindOf(step, workflow) {
  const type = step.data?.type;
  const known = workflow ? WORKFLOW[type] : null;
  return known ? { shape: known[0], kind: known[1] } : { shape: 'box', kind: typeof type === 'string' && type ? type : 'unknown' };
}

/** the marks of a step, one word each, only where attention is needed: untrusted, changed (since trusted), code (REQ-GA-027, D-426);
 *  a trusted step that holds no code and a data step carry none; `info` is the step's entry of IF-104 v2 `steps` */
export function marksOf(info) {
  if (!info || (info.kind !== 'transform' && info.kind !== 'master')) return [];
  return [info.trust !== 'trusted' && 'untrusted', info.changed_since_trusted && 'changed', info.code && 'code'].filter(Boolean);
}
