// PROTOTYPE CP6 (G-V4.VIEW, FR-53): the view settings in one place, remembered on this device; the viewer works with the defaults when they cannot be kept.
export const KEY = 'mia-graph-viewer-settings';
export const DEFAULTS = { physics: true, edges: 'rounded' };
const EDGES = ['rounded', 'straight'];

/** the saved settings, or the defaults when there are none, they are damaged, or the storage is not there (private window, blocked) */
export function loadSettings(storage) {
  try {
    const raw = storage?.getItem(KEY);
    if (!raw) return { ...DEFAULTS };
    const found = JSON.parse(raw);
    return { physics: typeof found.physics === 'boolean' ? found.physics : DEFAULTS.physics, edges: EDGES.includes(found.edges) ? found.edges : DEFAULTS.edges };
  } catch { return { ...DEFAULTS }; }
}

/** true when the settings were kept */
export function saveSettings(storage, settings) {
  try { storage.setItem(KEY, JSON.stringify(settings)); return true; } catch { return false; }
}

/** the vis edge options of a setting */
export const edgeSmooth = (settings) => (settings.edges === 'straight' ? false : { enabled: true, type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.6 });
