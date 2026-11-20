// PROTOTYPE CP4 (G-V4.GRAPHAPI.RULES, FR-64): what the owner is told when a run is tried. Pure.

/** one line per broken part: a rule with its steps or connections, or an input nobody supplies */
export function brokenLines(broken) {
  return (broken ?? []).map((b) => (b.kind === 'input' ? `input: step "${b.step}" reads "${b.input}", which has no writer, no start value and no value given with the run` : `${b.rule}: ${b.text} (${b.parts.join(', ')})`));
}

/** the status line after the run was tried; `status` is the HTTP status, `body` the answer */
export function runMessage(status, body) {
  if (status === 200) return `The checks passed; the stand-in steps ran in this order: ${(body.ran ?? []).join(', ') || '(no steps)'}.`;
  if (status === 422 && body?.status === 'refused') return `Run refused: no step ran. ${body.broken.length} broken part(s) are named under the status line.`;
  if (status === 403) return 'Only the owner can try a run.';
  if (status === 503) return 'The store cannot be reached: nothing was run.';
  return `The run was not tried (${status} ${body?.error ?? ''}).`;
}

/** the start values typed by the owner as a JSON object; {values} or {error} */
export function parseInputs(text) {
  if (!String(text ?? '').trim()) return { values: {} };
  try {
    const v = JSON.parse(text);
    return v && typeof v === 'object' && !Array.isArray(v) ? { values: v } : { error: 'The start values must be a JSON object, for example {"input.text": "hello"}.' };
  } catch { return { error: 'The start values are not valid JSON.' }; }
}
