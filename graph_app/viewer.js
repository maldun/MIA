// The graph viewer page (N-5, G-V4.VIEW, page-interface-note.md): the frame of the owner's layout (D-425) and the controller the page and the
// checks drive. Everything is read-only; the areas of later subgoals are present and empty (REQ-GA-013).
import { storeEntry, graphStatus } from './store-note.js';
import { filterGraphs, entryLabel } from './list-filter.js';
import { pictureOf } from './adapter.js';
import { problemText } from './problems.js';

/** the areas of a later subgoal: one line naming it, no control (REQ-GA-013) */
const LATER = {
  SEARCH: 'Search and chat about the open graph come with a later search subgoal.',
  EDIT: 'Adding and changing steps and connections comes with G-V4.EDIT.',
  REPLAY: 'Playing back the record of changes comes with G-V4.REPLAY.',
  RUN: 'Starting with input and the replay test area come with G-V4.GRAPHAPI.RUN.',
};

export function createViewer({ document, root, api, makeDrawing }) {      // `storage` comes in with the settings (T-10)
  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
    node.append(...children);
    return node;
  };
  const area = (tag, name, label, ...children) => el(tag, { 'data-area': name, 'aria-label': label, class: `area ${name}` }, el('h2', {}, label), ...children);
  const later = (name) => el('p', { 'data-later': name, class: 'later' }, LATER[name]);

  const filterBox = el('input', { id: 'graph-filter', type: 'search', 'aria-label': 'filter the graphs by name or description', placeholder: 'filter' });
  const list = el('ul', { class: 'graph-entries', 'aria-label': 'stored graphs' });
  const store = el('p', { 'data-store': '', class: 'store' }, 'store: asking ...');
  const status = el('p', { class: 'status-line', role: 'status' }, 'No graph open · read-only');
  const notice = el('p', { 'data-notice': 'store_unreachable', class: 'notice', role: 'alert' }, 'The store does not answer now; what is shown stays as it was.');
  const canvas = el('div', { class: 'drawing', 'data-drawing': '' });
  const problemList = el('ul', { class: 'problems', 'aria-label': 'what cannot be drawn' });
  root.replaceChildren(
    el('header', { class: 'top-band' },
      area('section', 'graph-list', 'Graphs', filterBox, list),
      area('section', 'search-band', 'Search and chat', later('SEARCH')),
      area('section', 'other-things', 'Other things', store)),
    el('div', { class: 'work' },
      area('aside', 'left-column', 'Selection', problemList, el('p', { class: 'hint' }, 'Nothing selected.')),
      el('div', { class: 'centre' },
        area('main', 'picture', 'Picture', canvas),
        area('section', 'actions-row', 'Actions', later('EDIT')))),
    area('section', 'history-row', 'History and replay', el('div', { class: 'later-parts' }, later('REPLAY'), later('RUN'))),
    area('footer', 'status-bar', 'Graph status', status));
  const statusBar = status.parentElement;
  let graphs = [];
  let typed = '';
  let drawing = null;
  let openId = null;

  /** a list entry: a tab stop of its own; Enter or a click opens it, the arrow keys move to the next or previous shown entry */
  function entry(g) {
    const item = el('li', { 'data-graph-id': g.id, class: 'graph-entry', tabindex: '0' }, entryLabel(g));
    item.addEventListener('click', () => controller.open(g.id));
    item.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') controller.open(g.id);
      if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
      const shown = list.children.filter((e) => !e.hidden);
      shown[shown.indexOf(item) + (event.key === 'ArrowDown' ? 1 : -1)]?.focus();
      event.preventDefault?.();
    });
    return item;
  }

  function showList() {
    const kept = new Set(filterGraphs(graphs, typed).map((g) => g.id));
    for (const item of list.children) item.hidden = !kept.has(item.dataset.graphId);
  }

  function markOpen() {
    for (const item of list.children) {
      if (item.dataset.graphId === openId) item.setAttribute('aria-current', 'true');
      else item.removeAttribute('aria-current');
    }
  }

  /** a refusal of IF-104 v2: no session asks for the login (REQ-GA-022), a store that does not answer keeps what is shown (REQ-GA-023) */
  function refused(err) {
    if (err?.status === 401) {
      graphs = [];
      openId = null;
      list.replaceChildren(el('li', { 'data-login': '', class: 'login' }, 'Not logged in. ', el('a', { href: '/' }, 'Log in through the main app'), '.'));
      canvas.hidden = true;
      status.textContent = 'No graph open · read-only';
      notice.remove();
      return;
    }
    if (err?.status === 503) {
      if (!notice.isConnected) statusBar.append(notice);
      return;
    }
    throw err;
  }

  function answered() {
    notice.remove();
    canvas.hidden = false;
  }

  /** the picture of the shown version, and what cannot be drawn named in the left column (REQ-GA-024 to 028) */
  function draw(shown) {
    drawing ??= makeDrawing(canvas);
    drawing.show(pictureOf(shown), {});
    problemList.replaceChildren(...(shown.problems ?? []).map((p) => el('li', { 'data-problem': p.problem }, problemText(p))));
  }

  filterBox.addEventListener('input', () => controller.filter(filterBox.value));

  const controller = {
    /** who is logged in, which store is read, and the list (REQ-GA-018, 019, 022, 023) */
    async start() {
      try {
        await api.me();
        store.textContent = `store: ${storeEntry(await api.store())}`;
        graphs = await api.listGraphs();
      } catch (err) {
        return refused(err);
      }
      answered();
      list.replaceChildren(...graphs.map(entry));
      showList();
      markOpen();
    },
    /** only the graphs whose ID or description holds every typed word (REQ-GA-020) */
    filter(text) {
      typed = text;
      showList();
    },
    /** the current version of a graph, drawn; the status bar names it (REQ-GA-017, 021) */
    async open(id) {
      let shown;
      try {
        shown = await api.readGraph(id);
      } catch (err) {
        return refused(err);
      }
      answered();
      openId = id;
      markOpen();
      status.textContent = graphStatus(shown);
      draw(shown);
    },
  };
  return controller;
}
