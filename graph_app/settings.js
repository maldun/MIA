// The view settings in one place, remembered on this device (R6, written again for REQ-GA-031, 034, 035). Pure apart from the storage handed in.
export const KEY = 'mia-graph-viewer-settings';
export const DEFAULTS = Object.freeze({ edges: 'rounded', arrangement: 'on' });
const CHOICES = { edges: ['rounded', 'straight'], arrangement: ['on', 'off'] };

/** one fixed seed and one fixed solver, so a graph without a saved arrangement settles the same way on every opening (REQ-GA-031) */
export const SEED = 7;
export const SOLVER = 'barnesHut';

/** only the known settings with known values; anything else is left out */
export function validSettings(found) {
  return Object.fromEntries(Object.entries(CHOICES).filter(([k, values]) => values.includes(found?.[k])).map(([k]) => [k, found[k]]));
}

/** the window's localStorage, or null when the browser refuses it (cookies and site data blocked: the getter throws SecurityError, V-9) */
export function pageStorage(win) {
  try {
    return win.localStorage;
  } catch {
    return null;
  }
}

/** the saved settings, or the defaults where there are none, they are damaged, or the storage is blocked (REQ-GA-035) */
export function loadSettings(storage) {
  try {
    return { ...DEFAULTS, ...validSettings(JSON.parse(storage.getItem(KEY) ?? '{}')) };
  } catch {
    return { ...DEFAULTS };
  }
}

/** true when the settings were kept; a blocked storage leaves the page working with what it has */
export function saveSettings(storage, settings) {
  try {
    storage.setItem(KEY, JSON.stringify(settings));
    return true;
  } catch {
    return false;
  }
}

/** the options the drawing gets (page-interface-note.md section 3) */
export function drawingOptions(settings, layout = 'settle') {
  return { edges: settings.edges, physics: settings.arrangement === 'on', seed: SEED, solver: SOLVER, layout };
}
