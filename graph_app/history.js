// The history of a graph and stepping between its versions (R6, written again for REQ-GA-038 to 040). Pure.

/** the versions newest first, each with who stored it and when and whether it is the current one (REQ-GA-038) */
export function historyEntries(versions, current) {
  return [...versions].sort((a, b) => b.version - a.version)
    .map((v) => ({ version: v.version, current: v.version === current, text: `version ${v.version} · ${v.author} · ${v.time}${v.version === current ? ' · current' : ''}` }));
}

/** the version one step older ('previous') or newer ('next') than `shown`; null beyond the oldest or the newest (REQ-GA-040) */
export function neighbour(versions, shown, direction) {
  const numbers = versions.map((v) => v.version).sort((a, b) => a - b);
  const i = numbers.indexOf(shown);
  const j = direction === 'previous' ? i - 1 : i + 1;
  return i >= 0 && j >= 0 && j < numbers.length ? numbers[j] : null;
}
