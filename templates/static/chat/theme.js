// Themes: dark, light, or auto (follows the system). The theme is the data-theme attribute of <html>;
// tokens.css does the rest. ?theme=light|dark|auto forces a theme for this page view (screenshots, tests).

export const THEMES = ['auto', 'dark', 'light'];

export function normalizeTheme(value) {
  return THEMES.includes(value) ? value : 'auto';
}

export function themeFromSearch(search = '') {
  const asked = new URLSearchParams(search).get('theme');
  return THEMES.includes(asked) ? asked : null;
}

/** the theme that is really shown: auto resolves to the system preference */
export function resolveTheme(setting, prefersLight) {
  const theme = normalizeTheme(setting);
  if (theme === 'auto') return prefersLight ? 'light' : 'dark';
  return theme;
}

export function initTheme({ storage, search = '', root = document.documentElement, onChange = () => {} }) {
  const forced = themeFromSearch(search);
  let setting = forced ?? normalizeTheme(storage.get('mia.theme', 'auto'));

  function apply() {
    root.dataset.theme = setting;
    onChange(setting);
  }

  apply();
  return {
    get: () => setting,
    set(value) {
      setting = normalizeTheme(value);
      if (!forced) storage.set('mia.theme', setting);
      apply();
    },
  };
}
