// The graph viewer page (N-5, G-V4.VIEW, page-interface-note.md): the frame of the owner's layout (D-425) and the controller the page and the
// checks drive. Everything is read-only; the areas of later subgoals are present and empty (REQ-GA-013).
import { storeEntry, graphStatus } from './store-note.js';

/** the areas of a later subgoal: one line naming it, no control (REQ-GA-013) */
const LATER = {
  SEARCH: 'Search and chat about the open graph come with a later search subgoal.',
  EDIT: 'Adding and changing steps and connections comes with G-V4.EDIT.',
  REPLAY: 'Playing back the record of changes comes with G-V4.REPLAY.',
  RUN: 'Starting with input and the replay test area come with G-V4.GRAPHAPI.RUN.',
};

export function createViewer({ document, root, api }) {      // `storage` and `makeDrawing` come in with the settings (T-10) and the picture (T-09)
  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
    node.append(...children);
    return node;
  };
  const area = (tag, name, label, ...children) => el(tag, { 'data-area': name, 'aria-label': label, class: `area ${name}` }, el('h2', {}, label), ...children);
  const later = (name) => el('p', { 'data-later': name, class: 'later' }, LATER[name]);

  const list = el('ul', { class: 'graph-entries', 'aria-label': 'stored graphs' });
  const store = el('p', { 'data-store': '', class: 'store' }, 'store: asking ...');
  const status = el('p', { class: 'status-line', role: 'status' }, 'No graph open · read-only');
  const canvas = el('div', { class: 'drawing' });
  root.replaceChildren(
    el('header', { class: 'top-band' },
      area('section', 'graph-list', 'Graphs', list),
      area('section', 'search-band', 'Search and chat', later('SEARCH')),
      area('section', 'other-things', 'Other things', store)),
    el('div', { class: 'work' },
      area('aside', 'left-column', 'Selection', el('p', { class: 'hint' }, 'Nothing selected.')),
      el('div', { class: 'centre' },
        area('main', 'picture', 'Picture', canvas),
        area('section', 'actions-row', 'Actions', later('EDIT')))),
    area('section', 'history-row', 'History and replay', el('div', { class: 'later-parts' }, later('REPLAY'), later('RUN'))),
    area('footer', 'status-bar', 'Graph status', status));

  function entry(g) {
    return el('li', { 'data-graph-id': g.id, class: 'graph-entry' },
      `${g.id} · ${g.kind} · version ${g.version} · ${g.steps} steps · ${g.connections} connections`);
  }

  return {
    /** who is logged in, which store is read, and the list (REQ-GA-018, 019) */
    async start() {
      await api.me();
      store.textContent = `store: ${storeEntry(await api.store())}`;
      list.replaceChildren(...(await api.listGraphs()).map(entry));
    },
    /** the current version of a graph; the status bar names it (REQ-GA-017) */
    async open(id) {
      status.textContent = graphStatus(await api.readGraph(id));
    },
  };
}
