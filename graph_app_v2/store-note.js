// PROTOTYPE CP9 (G-V4.EDIT, FR-95): what the owner is told about the live store and the copy. Pure.

/** the line for the header from the answer of /api/v2/status; empty when there is one store only */
export function storeNote(status) {
  if (!status || !status.split) return '';
  if (status.live !== 'reachable') return 'Live store: NOT REACHABLE. You can look at the copy; changing is not possible now.';
  const differing = Object.keys(status.differs ?? {});
  const warn = differing.length ? ` ${differing.length} graph(s) differ on the copy (${differing.join(', ')}): the live store wins at the next sync and the copy's versions are set aside, named.` : '';
  return (status.lag > 0 ? `Live store reachable. The copy is behind by ${status.lag} version(s): sync to see the changes.` : 'Live store reachable. The copy is up to date.') + warn;
}

/** what the owner is told after a sync: what was added, and which graphs had versions only the copy had and where they were put */
export function syncMessage(body) {
  const aside = Object.entries(body.set_aside ?? {});
  const added = `Synced: ${body.records} record(s) added to the copy.`;
  if (!aside.length) return added;
  return `${added} Set aside, because the live store wins: ${aside.map(([g, a]) => `${g} (version ${a.versions.join(', ')}) in ${a.file}`).join('; ')}.`;
}

/** whether the editor may be used: the live store is reachable (or there is one store only) */
export const canEdit = (status) => !status || !status.split || status.live === 'reachable';
