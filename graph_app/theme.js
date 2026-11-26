// The graph page shows the theme chosen in the main app on this device (REQ-GA-016, A-176, D-503). The main app saves its choice as
// `mia.theme` (templates/static/chat/theme.js); the page reads the same key, since both are served from one origin (/graph/ behind Caddy).
// tokens.css does the rest through data-theme on <html>; auto follows the system as before.

export const THEMES = ['auto', 'dark', 'light'];
export const THEME_KEY = 'mia.theme';
export const THEME_CHANGED = 'mia-theme-changed';      // fired after data-theme changed, so the picture re-colours from the new tokens

/** the saved choice; nothing, an unknown value or a blocked storage counts as auto */
export function chosenTheme(storage) {
  try {
    const value = storage?.getItem(THEME_KEY);
    return THEMES.includes(value) ? value : 'auto';
  } catch {
    return 'auto';
  }
}

function pageStorage(win) {
  try {
    return win.localStorage;
  } catch {
    return null;
  }
}

/** sets the theme now and again when another page of the origin (the main app in another tab) saves a new choice */
export function followTheme(win, root) {
  const apply = () => { root.dataset.theme = chosenTheme(pageStorage(win)); };
  apply();
  win.addEventListener?.('storage', (event) => {
    if (event.key !== THEME_KEY && event.key !== null) return;         // null: the whole storage was cleared
    apply();
    win.dispatchEvent?.(new (win.Event ?? Event)(THEME_CHANGED));
  });
}
