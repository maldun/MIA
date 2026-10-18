// Layout of the chat: panel at the right on wide screens (resizable, collapsible), bottom sheet with three
// snap heights on phones. CSS (layout.css) does the layout; this module sets variables and data attributes.
// The pure functions at the top are tested with node (tests/js/layout.test.mjs).

export const SNAPS = ['peek', 'half', 'full'];
export const GAP = 12;
export const PEEK_HEIGHT = 150;
export const MIN_PANEL = 320;
export const MAX_PANEL = 640;

/** same rule as the media query in layout.css: aspect ratio >= 1:1 and width >= 600 px */
export function layoutMode(width, height) {
  return width >= 600 && width >= height ? 'panel' : 'sheet';
}

export function clampPanelWidth(width, viewportWidth) {
  const max = Math.max(MIN_PANEL, Math.min(MAX_PANEL, viewportWidth - 2 * GAP - 120));
  return Math.round(Math.min(Math.max(width, MIN_PANEL), max));
}

/** pixel heights of the sheet snaps */
export function snapHeights(viewportHeight, bottomInset = 0) {
  return {
    peek: PEEK_HEIGHT + bottomInset,
    half: Math.round(viewportHeight * 0.52),
    full: Math.round(viewportHeight * 0.9),
  };
}

export function nearestSnap(height, viewportHeight, bottomInset = 0) {
  const heights = snapHeights(viewportHeight, bottomInset);
  let best = 'half';
  let distance = Infinity;
  for (const snap of SNAPS) {
    const d = Math.abs(heights[snap] - height);
    if (d < distance) {
      distance = d;
      best = snap;
    }
  }
  return best;
}

/** one step up (+1) or down (-1) through the snaps */
export function nextSnap(snap, direction) {
  const index = SNAPS.indexOf(snap);
  const start = index < 0 ? 1 : index;
  return SNAPS[Math.min(SNAPS.length - 1, Math.max(0, start + Math.sign(direction)))];
}

/** how much of the window the panel covers at the right (the character is centered in the rest) */
export function occupiedWidth({ mode, collapsed, panelWidth }) {
  return mode === 'panel' && !collapsed ? panelWidth + 2 * GAP : 0;
}

/** the part of the window the chat covers, in pixels: the character is centered in the rest ({"type": "viewport_inset"}) */
export function insetFor({ mode, collapsed, rect, width, height, top = 0 }) {
  const inset = { left: 0, right: 0, top: Math.max(0, Math.round(top)), bottom: 0, width, height };      // top: the mood line
  if (collapsed || !rect) return inset;
  if (mode === 'panel') inset.right = Math.max(0, Math.round(width - rect.left));
  else inset.bottom = Math.max(0, Math.round(height - rect.top));
  return inset;
}

function numberOr(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

export function initLayout({ storage, panel, resizeHandle, sheetHandle, collapseButton, openButton, moodChip = null, root = document.documentElement, win = window }) {
  const body = document.body;
  let panelWidth = clampPanelWidth(numberOr(storage.get('mia.panelWidth'), 420), win.innerWidth);
  let snap = SNAPS.includes(storage.get('mia.snap')) ? storage.get('mia.snap') : 'half';
  let collapsed = storage.get('mia.collapsed') === '1';
  let listeners = [];

  const mode = () => layoutMode(win.innerWidth, win.innerHeight);

  function apply() {
    root.style.setProperty('--panel-w', `${panelWidth}px`);
    body.dataset.snap = snap;
    panel.dataset.collapsed = String(collapsed);
    openButton.hidden = !collapsed;
    root.style.setProperty('--occupied-w', `${occupiedWidth({ mode: mode(), collapsed, panelWidth })}px`);
    for (const listener of listeners) listener({ mode: mode(), collapsed, panelWidth, snap });
  }

  function setCollapsed(value) {
    collapsed = value;
    storage.set('mia.collapsed', collapsed ? '1' : '0');
    apply();
    (collapsed ? openButton : collapseButton).focus?.();
  }

  // --- wide: drag the left edge of the panel ---------------------------------------------------
  function dragWidth(event) {
    panelWidth = clampPanelWidth(win.innerWidth - event.clientX - GAP, win.innerWidth);
    apply();
  }

  resizeHandle.addEventListener('pointerdown', (event) => {
    resizeHandle.setPointerCapture(event.pointerId);
    body.dataset.dragging = 'true';
    const move = (e) => dragWidth(e);
    const up = () => {
      resizeHandle.removeEventListener('pointermove', move);
      resizeHandle.removeEventListener('pointerup', up);
      resizeHandle.removeEventListener('pointercancel', up);
      delete body.dataset.dragging;
      storage.set('mia.panelWidth', panelWidth);
    };
    resizeHandle.addEventListener('pointermove', move);
    resizeHandle.addEventListener('pointerup', up);
    resizeHandle.addEventListener('pointercancel', up);
  });

  resizeHandle.addEventListener('keydown', (event) => {
    const step = event.shiftKey ? 48 : 16;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      panelWidth = clampPanelWidth(panelWidth + (event.key === 'ArrowLeft' ? step : -step), win.innerWidth);
      storage.set('mia.panelWidth', panelWidth);
      apply();
      event.preventDefault();
    }
  });

  // --- phone: drag the handle of the sheet, or step with the keyboard -------------------------------------
  sheetHandle.addEventListener('pointerdown', (event) => {
    sheetHandle.setPointerCapture(event.pointerId);
    body.dataset.dragging = 'true';
    const startY = event.clientY;
    const startHeight = panel.getBoundingClientRect().height;
    const move = (e) => {
      const height = Math.min(win.innerHeight * 0.92, Math.max(100, startHeight - (e.clientY - startY)));
      root.style.setProperty('--sheet-h', `${height}px`);
    };
    const up = (e) => {
      sheetHandle.removeEventListener('pointermove', move);
      sheetHandle.removeEventListener('pointerup', up);
      sheetHandle.removeEventListener('pointercancel', up);
      delete body.dataset.dragging;
      const height = panel.getBoundingClientRect().height;
      root.style.removeProperty('--sheet-h');
      snap = nearestSnap(height, win.innerHeight);
      storage.set('mia.snap', snap);
      apply();
    };
    sheetHandle.addEventListener('pointermove', move);
    sheetHandle.addEventListener('pointerup', up);
    sheetHandle.addEventListener('pointercancel', up);
  });

  sheetHandle.addEventListener('keydown', (event) => {
    const direction = { ArrowUp: 1, ArrowDown: -1, Enter: 1, ' ': 1 }[event.key];
    if (direction === undefined) return;
    snap = event.key === 'Enter' || event.key === ' ' ? (snap === 'full' ? 'peek' : nextSnap(snap, 1)) : nextSnap(snap, direction);
    storage.set('mia.snap', snap);
    apply();
    event.preventDefault();
  });

  collapseButton.addEventListener('click', () => setCollapsed(true));
  openButton.addEventListener('click', () => setCollapsed(false));

  // the on-screen keyboard: the sheet sits above it (visual viewport)
  const viewport = win.visualViewport;
  function keyboard() {
    if (!viewport) return;
    const covered = Math.max(0, win.innerHeight - viewport.height - viewport.offsetTop);
    root.style.setProperty('--kb', `${Math.round(covered)}px`);
  }
  viewport?.addEventListener('resize', keyboard);
  viewport?.addEventListener('scroll', keyboard);
  win.addEventListener('resize', () => {
    panelWidth = clampPanelWidth(panelWidth, win.innerWidth);
    apply();
  });

  apply();
  return {
    mode,
    inset: () => insetFor({ mode: mode(), collapsed, rect: panel.getBoundingClientRect(), width: win.innerWidth, height: win.innerHeight, top: moodChip && !moodChip.hidden ? moodChip.getBoundingClientRect().bottom + 6 : 0 }),
    get collapsed() { return collapsed; },
    get snap() { return snap; },
    get panelWidth() { return panelWidth; },
    setCollapsed,
    setSnap(value) { snap = SNAPS.includes(value) ? value : snap; storage.set('mia.snap', snap); apply(); },
    onChange(listener) { listeners.push(listener); },
  };
}
