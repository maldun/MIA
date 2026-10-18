// The menu in the panel header: sound, theme, editor, about.

export function initMenu({ button, menu, themeButtons, theme, aboutButton, aboutDialog, aboutClose }) {
  function open() {
    menu.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    menu.querySelector('button, a')?.focus();
  }

  function close(returnFocus = true) {
    if (menu.hidden) return;
    menu.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    if (returnFocus) button.focus();
  }

  function markTheme() {
    for (const choice of themeButtons) {
      choice.setAttribute('aria-pressed', String(choice.dataset.themeChoice === theme.get()));
    }
  }

  button.addEventListener('click', () => (menu.hidden ? open() : close()));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !menu.hidden) close();
  });
  document.addEventListener('pointerdown', (event) => {
    if (!menu.hidden && !menu.contains(event.target) && !button.contains(event.target)) close(false);
  });

  for (const choice of themeButtons) {
    choice.addEventListener('click', () => {
      theme.set(choice.dataset.themeChoice);
      markTheme();
    });
  }

  aboutButton.addEventListener('click', () => {
    close(false);
    aboutDialog.showModal();
  });
  aboutClose.addEventListener('click', () => aboutDialog.close());

  markTheme();
  return { open, close };
}
