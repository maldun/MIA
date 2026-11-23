// The page entry of the graph viewer (N-5, G-V4.VIEW, page-interface-note.md section 1): the viewer on IF-104 v2 of this backend.
import { createViewer } from './viewer.js';
import { httpApi } from './api.js';
import { visDrawing } from './drawing.js';

createViewer({
  document,
  root: document.getElementById('app'),
  api: httpApi((url, init) => fetch(url, { credentials: 'same-origin', ...init })),
  storage: localStorage,
  makeDrawing: (container) => visDrawing(container, globalThis.vis),
}).start();
