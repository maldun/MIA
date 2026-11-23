// The page's reader of IF-104 v2 (G-V4.VIEW, page-interface-note.md section 1): GETs only; a non-200 answer rejects with {status, code, detail}.

export function httpApi(fetchFn, base = '/api/v2') {
  async function get(path) {
    const answer = await fetchFn(base + path);
    const body = await answer.json().catch(() => ({}));
    if (answer.status !== 200) {
      const { error, ...detail } = body ?? {};
      throw { status: answer.status, code: error ?? null, detail };
    }
    return body;
  }
  const graph = (id) => `/graphs/${encodeURIComponent(id)}`;
  return {
    me: () => get('/me'),
    store: () => get('/store'),
    listGraphs: () => get('/graphs'),
    readGraph: (id, version) => get(graph(id) + (version === undefined || version === null ? '' : `?version=${version}`)),
    versions: (id) => get(`${graph(id)}/versions`),
    readArrangement: (id) => get(`${graph(id)}/arrangement`),
  };
}
