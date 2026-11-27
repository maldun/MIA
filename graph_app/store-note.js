// What the page says about the store it reads (REQ-GA-018, IF-104 v2 route 2). Pure; text only, never a control.

/** "files, reachable" or "database, not reachable"; the copy is named once G-V4.GRAPHSTORE.TRANSFER shows one (`shown` = copy) */
export function storeEntry(answer) {
  const line = `${answer.store}, ${answer.reachable ? 'reachable' : 'not reachable'}`;
  return answer.shown === 'copy' ? `${line}; showing the copy` : line;
}

/** the status bar line of a shown graph: ID, kind, version (and the newest when an older one is shown), who stored it and when, read-only */
export function graphStatus({ graph, version, current, author, time }) {
  const which = version === current ? `version ${version}` : `version ${version} of ${current}`;
  return `${graph.id} · ${graph.kind ?? 'workflow'} · ${which} · stored by ${author} · ${time} · read-only`;
}
