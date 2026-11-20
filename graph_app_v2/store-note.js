// PROTOTYPE CP9 (G-V4.EDIT, FR-95): what the owner is told about the live store and the copy. Pure.

/** the line for the header from the answer of /api/v2/status; empty when there is one store only */
export function storeNote(status) {
  if (!status || !status.split) return '';
  if (status.live !== 'reachable') return 'Live store: NOT REACHABLE. You can look at the copy; changing is not possible now.';
  return status.lag > 0 ? `Live store reachable. The copy is behind by ${status.lag} version(s): sync to see the changes.` : 'Live store reachable. The copy is up to date.';
}

/** whether the editor may be used: the live store is reachable (or there is one store only) */
export const canEdit = (status) => !status || !status.split || status.live === 'reachable';
