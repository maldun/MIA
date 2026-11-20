// PROTOTYPE CP9 (G-V4.EDIT, FR-91): undo and redo of the changes made in one editing session, before anything is kept. Pure and immutable; nothing is stored or recorded.
export const create = (graph) => ({ past: [], present: graph, future: [] });
export const push = (h, graph) => ({ past: [...h.past, h.present], present: graph, future: [] });
export const undo = (h) => (h.past.length ? { past: h.past.slice(0, -1), present: h.past[h.past.length - 1], future: [h.present, ...h.future] } : h);
export const redo = (h) => (h.future.length ? { past: [...h.past, h.present], present: h.future[0], future: h.future.slice(1) } : h);
export const canUndo = (h) => h.past.length > 0;
export const canRedo = (h) => h.future.length > 0;

/** what the owner is told about the session: how many changes can be undone or redone */
export const note = (h) => `${h.past.length} change(s) to undo, ${h.future.length} to redo`;
