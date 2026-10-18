// Per-device settings (ui/REQUIREMENTS_CHAT.md, 8). Everything is stored in localStorage through the safe storage wrapper.
// The settings are applied as data attributes / CSS variables on <html>, so the styles do the rest.

export const DEFAULTS = Object.freeze({
  accent: 218,          // hue (0-360) of the accent color
  sendOnEnter: true,    // false: Enter makes a new line, only the button sends
  emotions: true,       // emotion badge next to MIA's name
  mood: true,           // mood line above the character
  timestamps: true,     // time under each message
  compact: false,       // denser spacing
});

export const ACCENTS = Object.freeze([218, 262, 330, 8, 32, 150, 190]);
const PREFIX = 'mia.setting.';

export function clampHue(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(360, Math.max(0, Math.round(n))) : DEFAULTS.accent;
}

function parse(key, raw) {
  if (raw === null || raw === undefined) return DEFAULTS[key];
  if (key === 'accent') return clampHue(raw);
  return raw === '1';
}

export function loadSettings(storage) {
  const settings = {};
  for (const key of Object.keys(DEFAULTS)) settings[key] = parse(key, storage.get(PREFIX + key));
  return settings;
}

/** writes the settings into the document: data attributes for the switches, a variable for the hue */
export function applySettings(settings, root = document.documentElement) {
  root.style.setProperty('--accent-h', String(settings.accent));
  root.dataset.emotions = settings.emotions ? '1' : '0';
  root.dataset.mood = settings.mood ? '1' : '0';
  root.dataset.timestamps = settings.timestamps ? '1' : '0';
  root.dataset.compact = settings.compact ? '1' : '0';
}

export function initSettings({ storage, root = document.documentElement, onChange = () => {} }) {
  let settings = loadSettings(storage);
  applySettings(settings, root);
  return {
    get: () => ({ ...settings }),
    set(key, value) {
      if (!(key in DEFAULTS)) return;
      settings = { ...settings, [key]: key === 'accent' ? clampHue(value) : Boolean(value) };
      storage.set(PREFIX + key, typeof settings[key] === 'boolean' ? (settings[key] ? '1' : '0') : settings[key]);
      applySettings(settings, root);
      onChange(settings, key);
    },
    /** back to the defaults; the keys of other modules (theme, view, sound, layout) go too when listed */
    reset(extraKeys = []) {
      for (const key of Object.keys(DEFAULTS)) storage.remove(PREFIX + key);
      for (const key of extraKeys) storage.remove(key);
      settings = loadSettings(storage);
      applySettings(settings, root);
      onChange(settings, null);
    },
  };
}
