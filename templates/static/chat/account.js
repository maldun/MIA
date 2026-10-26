// The account dialog (REQ-CLV-014): who is logged in (the account of a kept session) and the change of the user's own password.
import { passwordProblem } from './panels-model.js';

export function initAccount({ dialog, nameEl, form, oldInput, newInput, repeatInput, errorLine, closeButton, api, storage, t, notify = () => {} }) {
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
  closeButton.addEventListener('click', () => dialog.close());
  return { open };
}
