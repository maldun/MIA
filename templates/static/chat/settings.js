// Settings of this device (ui/REQUIREMENTS_CHAT.md 8): kept in localStorage (wrapped, see storage.js), applied as
// data attributes on <html> so CSS does the work. Theme, sound, panel size and the drafts have their own keys.

export const DEFAULTS = Object.freeze({
  enterSends: 'auto',      // auto: Enter sends with a mouse, new line on touch screens; enter / newline: always
  showEmotions: true,
  showMood: true,
  showTimes: true,
  compact: false,
});

export const ENTER_MODES = ['auto', 'enter', 'newline'];
const KEY = 'mia.settings';

/** anything that is not a valid value falls back to the default (old or damaged data never breaks the page) */
export function normalizeSettings(raw) {
  const source = raw && typeof raw === 'object' ? raw : {};
  const result = { ...DEFAULTS };
  if (ENTER_MODES.includes(source.enterSends)) result.enterSends = source.enterSends;
  for (const key of ['showEmotions', 'showMood', 'showTimes', 'compact']) {
    if (typeof source[key] === 'boolean') result[key] = source[key];
  }
  return result;
}

/** does Enter send the message? */
export function enterSends(mode, coarsePointer) {
  if (mode === 'enter') return true;
  if (mode === 'newline') return false;
  return !coarsePointer;
}

function load(storage) {
  try {
    return normalizeSettings(JSON.parse(storage.get(KEY, '{}')));
  } catch (error) {
    return { ...DEFAULTS };
  }
}

export function initSettings({ storage, root = document.documentElement, onChange = () => {} }) {
  let current = load(storage);

  function apply() {
    root.dataset.compact = String(current.compact);
    root.dataset.emotions = String(current.showEmotions);
    root.dataset.times = String(current.showTimes);
    onChange({ ...current });
  }

  apply();
  return {
    get: () => ({ ...current }),
    set(key, value) {
      current = normalizeSettings({ ...current, [key]: value });
      storage.set(KEY, JSON.stringify(current));
      apply();
    },
    reset() {
      current = { ...DEFAULTS };
      storage.remove(KEY);
      apply();
    },
  };
}
