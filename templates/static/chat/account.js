// The account dialog (REQ-CLV-014, REQ-CLV-022): who is logged in (the account of a kept session), the change of the user's own password and the logout.
// A password goes only over HTTPS or to this computer, as at the login (REQ-CLV-018).
import { passwordProblem } from './panels-model.js';
import { secureChannel } from './login.js';

export function initAccount({ dialog, nameEl, form, oldInput, newInput, repeatInput, errorLine, closeButton, logoutButton, api, storage, t, socket = null, location = globalThis.location, notify = () => {}, onLoggedOut = () => {} }) {
  function show(key) {
    errorLine.textContent = key ? t(key) : '';
    errorLine.hidden = !key;
  }

  async function open() {
    show('');
    form.reset();
    dialog.showModal();
    try {
      const { user } = await api.whoami();
      nameEl.textContent = user;
      storage.set('mia.account', user);
    } catch (error) {
      nameEl.textContent = storage.get('mia.account', '') || '';
    }
    oldInput.focus();
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const problem = passwordProblem(oldInput.value, newInput.value, repeatInput.value);
    if (problem) { show(`account.${problem}`); return; }
    if (!secureChannel(location)) { show('login.insecure'); return; }      // F7: nothing is sent, the server would refuse it after reading both
    try {
      await api.changePassword(oldInput.value, newInput.value);
    } catch (error) {
      show(error.code === 'bad_credentials' ? 'account.wrong_old' : error.code === 'weak_password' ? 'account.short' : error.status === 0 ? 'chat.offline' : 'account.failed');
      return;
    }
    form.reset();                                          // the passwords are never kept in the page
    dialog.close();
    notify(t('account.changed'));
  });
  logoutButton.addEventListener('click', async () => {
    try {
      await api.logout();
    } catch (error) {
      // a session that is already gone is as good as a logout; any other failure keeps the user logged in and says so
      // (the button is in the menu, the dialog is not open: the failure comes as a message)
      if (error.status !== 401) { notify(t(error.status === 0 ? 'chat.offline' : 'account.logout_failed')); return; }
    }
    form.reset();
    dialog.close();
    socket?.disconnect();                                  // the server ended the session; the socket would be refused anyway
    onLoggedOut();
  });
  closeButton.addEventListener('click', () => dialog.close());
  return { open };
}
