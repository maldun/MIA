// The login of the page (IF-101 `login`, REQ-CLV-014, -015, -018). The server answers with a session cookie (HttpOnly, same site), so the page keeps no token:
// the history and the socket carry the cookie by themselves. The password is sent once, only over HTTPS or to localhost.

const LOCAL_HOSTS = ['localhost', '127.0.0.1', '[::1]', '::1'];

/** may a password travel here? HTTPS, or a local address over plain HTTP */
export function secureChannel({ protocol, hostname }) {
  return protocol === 'https:' || LOCAL_HOSTS.includes(hostname);
}

/** the text key for what went wrong */
export function loginErrorKey(error) {
  return { bad: 'login.bad', throttled: 'login.throttled', insecure: 'login.insecure', empty: 'login.empty' }[error] ?? 'login.failed';
}

/** one login attempt: {ok: true, user} or {ok: false, error: 'bad' | 'throttled' | 'insecure' | 'empty' | 'failed'} */
export async function submitLogin({ user, password, location = window.location, fetchFn = (url, init) => fetch(url, init) }) {
  if (!user || !password) return { ok: false, error: 'empty' };
  if (!secureChannel(location)) return { ok: false, error: 'insecure' };
  try {
    const response = await fetchFn(new URL('/api/login', location.origin), {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user, password }),
    });
    if (response.ok) return { ok: true, user };
    return { ok: false, error: { 401: 'bad', 429: 'throttled' }[response.status] ?? 'failed' };
  } catch (error) {
    return { ok: false, error: 'failed' };
  }
}

/**
 * The login dialog: shown when the server says the session is missing (history or socket answer "unauthenticated").
 * Over a channel that is not secure the form is switched off and says why, nothing is sent.
 */
export function initLogin({ dialog, form, userInput, passwordInput, errorLine, submitButton, storage, t, onSuccess, win = window }) {
  const channelOk = secureChannel(win.location);

  function show(key) {
    errorLine.textContent = key ? t(key) : '';
    errorLine.hidden = !key;
  }

  function open() {
    if (dialog.open) return;
    show(channelOk ? '' : 'login.insecure');
    userInput.disabled = passwordInput.disabled = submitButton.disabled = !channelOk;
    userInput.value = storage.get('mia.account', '') || '';
    dialog.showModal();
    (userInput.value ? passwordInput : userInput).focus();
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    submitButton.disabled = true;
    const result = await submitLogin({ user: userInput.value.trim(), password: passwordInput.value, location: win.location });
    passwordInput.value = '';                         // never kept in the page
    submitButton.disabled = !channelOk;
    if (result.ok) {
      storage.set('mia.account', result.user);
      dialog.close();
      onSuccess(result.user);
      return;
    }
    show(loginErrorKey(result.error));
    passwordInput.focus();
  });
  dialog.addEventListener('cancel', (event) => event.preventDefault());       // there is no chat without a login

  return { open };
}
