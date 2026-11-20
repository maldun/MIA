// PROTOTYPE CP7 (G-V4.VIEW, FR-55): the history of a graph as a list to scroll through, and stepping to the previous and the next version. Pure helpers.

/** the entries newest first: [{version, text, current}] with who and when */
export function historyEntries(versions, current) {
  return [...versions].sort((a, b) => b.version - a.version).map((v) => ({
    version: v.version, current: v.version === current,
    text: `version ${v.version}${v.version === current ? ' (current)' : ''}  ${v.author}  ${String(v.time ?? '').replace('T', ' ').replace('Z', '')}`,
  }));
}

/** the version to step to from `shown`: 'previous' = the next older one, 'next' = the next newer one; null at the ends */
export function neighbour(versions, shown, direction) {
  const numbers = versions.map((v) => v.version).sort((a, b) => a - b);
  const i = numbers.indexOf(shown);
  if (i < 0) return null;
  const j = direction === 'previous' ? i - 1 : i + 1;
  return j >= 0 && j < numbers.length ? numbers[j] : null;
}

/** the line that says which version is shown */
export const versionNote = (shown, current) => (shown === current ? `version ${shown} (the current one)` : `version ${shown} of ${current}: an earlier version, read-only`);
