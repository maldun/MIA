// The REST calls of IF-101 v1 (contracts/IF-101-chat-api.md): one function per operation. The session is the cookie of the login; a request
// without a session (401 `unauthenticated`) asks for the login. Chat messages, stop and the live events travel over the socket (chat.js).

export class ApiError extends Error {
  constructor(status, code, rule = null) {
    super(`${status} ${code}${rule ? `: ${rule}` : ''}`);
    this.status = status;
    this.code = code;
    this.rule = rule;
  }
}

export function createApi({ origin = location.origin, fetchFn = (url, init) => fetch(url, init), onLoginRequired = () => {} } = {}) {
  async function request(method, path, { query, body } = {}) {
    const url = new URL(path, origin);
    for (const [key, value] of Object.entries(query ?? {})) url.searchParams.set(key, value);
    let response;
    try {
      response = await fetchFn(url, {
        method,
        credentials: 'same-origin',
        headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (error) {
      throw new ApiError(0, 'offline');
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401 && data?.error === 'unauthenticated') onLoginRequired();
      throw new ApiError(response.status, data?.error ?? 'failed', data?.rule ?? null);
    }
    return data;
  }

  return {
    whoami: () => request('GET', '/api/whoami'),
    logout: () => request('POST', '/api/logout'),
    changePassword: (oldPassword, newPassword) => request('POST', '/api/change_password', { body: { old: oldPassword, new: newPassword } }),
    regenerate: (messageId) => request('POST', '/api/regenerate', { body: { message_id: messageId } }),
    speakAgain: (messageId) => request('POST', '/api/speak_again', { body: { message_id: messageId } }),
    account: (messageId) => request('GET', '/api/account', { query: { message_id: messageId } }),
    vote: (subject, category, value) => request('POST', '/api/vote', { body: { subject, category, value } }),
    score: () => request('GET', '/api/score'),
    items: (kind) => request('GET', '/api/items', { query: { kind } }),
    saveItem: (kind, id, text, source) => request('POST', '/api/items', { body: { kind, id, text, source } }),
    deleteItem: (kind, id) => request('DELETE', '/api/items', { query: { kind, id } }),
    trust: () => request('GET', '/api/trust'),
    setTrust: (source, value) => request('POST', '/api/trust', { body: { source, value } }),
    persona: () => request('GET', '/api/persona'),
    savePersona: (doc) => request('POST', '/api/persona', { body: { doc } }),
  };
}
