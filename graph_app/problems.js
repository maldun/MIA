// What cannot be drawn (R6, written again for REQ-GA-025 and IF-104 v2 `problems`). Pure.

/** the IDs of the steps that connections name but the graph does not have, in the order the problems name them */
export function missingSteps(problems) {
  return [...new Set(problems.filter((p) => p.problem === 'missing_step').map((p) => p.step))];
}

/** each problem in words, for the left column */
export function problemText(p) {
  if (p.problem === 'missing_step') return `connection ${p.connection}: its ${p.end === 'to' ? 'end' : 'start'} step ${p.step} does not exist`;
  if (p.problem === 'duplicate_step') return `step ${p.step}: the ID is used more than once`;
  return `${p.problem}`;
}
