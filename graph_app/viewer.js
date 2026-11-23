// The graph viewer page (N-5, G-V4.VIEW, page-interface-note.md): the frame of the owner's layout (D-425) and the controller the page and the
// checks drive. Everything is read-only; the areas of later subgoals are present and empty (REQ-GA-013).
import { storeEntry, graphStatus } from './store-note.js';
import { filterGraphs, entryLabel } from './list-filter.js';
import { pictureOf } from './adapter.js';
import { problemText } from './problems.js';
import { placed, layered } from './arrangement.js';
import { loadSettings, saveSettings, validSettings, drawingOptions } from './settings.js';
import { kindOf, isWorkflow } from './step-marks.js';
import { stepFields, connectionFields, storedText } from './panel.js';
import { historyEntries, neighbour } from './history.js';

/** the areas of a later subgoal: one line naming it, no control (REQ-GA-013) */
const LATER = {
  SEARCH: 'Search and chat about the open graph come with a later search subgoal.',
  EDIT: 'Adding and changing steps and connections comes with G-V4.EDIT.',
  REPLAY: 'Playing back the record of changes comes with G-V4.REPLAY.',
  RUN: 'Starting with input and the replay test area come with G-V4.GRAPHAPI.RUN.',
};

export function createViewer({ document, root, api, storage, makeDrawing }) {
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
  const hint = el('p', { class: 'hint' }, 'Nothing selected.');
  const selection = el('div', { class: 'selection' }, hint);
  const stepList = el('ul', { class: 'step-list', 'aria-label': 'steps of the shown graph' });
  const historyOpen = el('button', { id: 'history-open', type: 'button', disabled: '' }, 'History');
  const previousButton = el('button', { id: 'history-previous', type: 'button', disabled: '' }, 'Previous version');
  const nextButton = el('button', { id: 'history-next', type: 'button', disabled: '' }, 'Next version');
  const historyList = el('ul', { class: 'history-list', 'aria-label': 'versions, newest first' });
  let settings = loadSettings(storage);
  const choice = (name, label, values) => el('label', { class: 'setting' }, `${label} `,
    el('select', { 'data-setting': name }, ...values.map((v) => el('option', { value: v }, v))));
  const settingsOpen = el('button', { id: 'settings-open', type: 'button', 'aria-expanded': 'false', 'aria-controls': 'view-settings' }, 'View settings');
  const settingsPlace = el('div', { id: 'view-settings', 'data-settings': '', class: 'settings', role: 'group', 'aria-label': 'view settings' },
    choice('edges', 'Connections', ['rounded', 'straight']), choice('arrangement', 'Arrange by itself', ['on', 'off']),
    el('button', { id: 'layered-reset', type: 'button' }, 'Reset to layers'));
  settingsPlace.hidden = true;
  root.replaceChildren(
    el('header', { class: 'top-band' },
      area('section', 'graph-list', 'Graphs', filterBox, list),
      area('section', 'search-band', 'Search and chat', later('SEARCH')),
      area('section', 'other-things', 'Other things', store, settingsOpen, settingsPlace)),
    el('div', { class: 'work' },
      area('aside', 'left-column', 'Selection', problemList, selection, el('h3', {}, 'Steps'), stepList),
      el('div', { class: 'centre' },
        area('main', 'picture', 'Picture', canvas),
        area('section', 'actions-row', 'Actions', later('EDIT')))),
    area('section', 'history-row', 'History and replay',
      el('div', { class: 'history' }, el('div', { class: 'history-buttons' }, historyOpen, previousButton, nextButton), historyList),
      el('div', { class: 'later-parts' }, later('REPLAY'), later('RUN'))),
    area('footer', 'status-bar', 'Graph status', status));
  const statusBar = status.parentElement;
  let graphs = [];
  let typed = '';
  let drawing = null;
  let openId = null;
  let picture = null;      // what the drawing got for the open version, before places
  let saved = null;        // the saved arrangement of the open graph (REQ-GA-030)
  let moved = {};          // where the owner dropped steps while this graph is open (REQ-GA-032)
  let shown = null;        // the read answer of the version shown (REQ-GA-036, 039)
  let versions = null;     // the versions of the open graph, once its history is opened (REQ-GA-038)

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

  function theDrawing() {
    if (!drawing) {
      drawing = makeDrawing(canvas);
      drawing.onDragEnd(({ id, x, y }) => { moved[id] = { x: Math.round(x), y: Math.round(y) }; });
    }
    return drawing;
  }

  /** the picture of the shown version at its places; what cannot be drawn and the steps listed in the left column (REQ-GA-024 to 031) */
  function draw() {
    picture = pictureOf(shown);
    theDrawing().show({ nodes: placed(picture.nodes, saved, moved), edges: picture.edges }, drawingOptions(settings));
    problemList.replaceChildren(...(shown.problems ?? []).map((p) => el('li', { 'data-problem': p.problem }, problemText(p))));
    stepList.replaceChildren(...picture.nodes.map((n) => stepEntry(n.id)));
    selection.replaceChildren(hint);
    status.textContent = graphStatus(shown);
  }

  /** a step of the step list: the other way to a step besides the picture, by Tab, the arrow keys and Enter (REQ-GA-041) */
  function stepEntry(id) {
    const item = el('li', { 'data-step-id': id, class: 'step-entry', tabindex: '0' }, id);
    item.addEventListener('click', () => controller.selectStep(id));
    item.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') controller.selectStep(id);
      if (event.key === 'ArrowDown') item.nextElementSibling?.focus();
      if (event.key === 'ArrowUp') item.previousElementSibling?.focus();
    });
    return item;
  }

  /** the selection's fields as `label: value` and its stored text, all as text (REQ-GA-029, 036) */
  function showSelection(heading, fields, stored) {
    selection.replaceChildren(el('h3', {}, heading),
      ...fields.map(([name, label, value]) => el('p', { 'data-field': name, class: 'field' }, `${label}: ${value}`)),
      el('pre', { 'data-stored-text': '', class: 'stored-text' }, storedText(stored)));
  }

  function showHistory() {
    const number = shown?.version;
    historyList.replaceChildren(...(versions ? historyEntries(versions, shown.current) : []).map((v) => {
      const item = el('li', { 'data-version': String(v.version), 'data-current': String(v.current), class: 'history-entry', tabindex: '0' }, v.text);
      if (v.version === number) item.setAttribute('aria-selected', 'true');
      item.addEventListener('click', () => controller.showVersion(v.version));
      item.addEventListener('keydown', (event) => { if (event.key === 'Enter') controller.showVersion(v.version); });
      return item;
    }));
    const offer = (button, on) => (on ? button.removeAttribute('disabled') : button.setAttribute('disabled', ''));
    offer(historyOpen, openId !== null);
    offer(previousButton, Boolean(versions) && neighbour(versions, number, 'previous') !== null);
    offer(nextButton, Boolean(versions) && neighbour(versions, number, 'next') !== null);
  }

  function showSettings() {
    for (const select of settingsPlace.querySelectorAll('[data-setting]')) select.value = settings[select.dataset.setting];
  }

  filterBox.addEventListener('input', () => controller.filter(filterBox.value));
  settingsOpen.addEventListener('click', () => {
    settingsPlace.hidden = !settingsPlace.hidden;
    settingsOpen.setAttribute('aria-expanded', String(!settingsPlace.hidden));
  });
  for (const select of settingsPlace.querySelectorAll('[data-setting]')) {
    select.addEventListener('change', () => controller.setSettings({ [select.dataset.setting]: select.value }));
  }
  settingsPlace.querySelector('#layered-reset').addEventListener('click', () => controller.layered());
  historyOpen.addEventListener('click', () => controller.openHistory());
  previousButton.addEventListener('click', () => controller.previous());
  nextButton.addEventListener('click', () => controller.next());
  showSettings();

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
    /** the current version of a graph with its saved arrangement, drawn; the status bar names it (REQ-GA-017, 021, 030) */
    async open(id) {
      let answer;
      let arrangement;
      try {
        [answer, arrangement] = await Promise.all([api.readGraph(id), api.readArrangement(id)]);
      } catch (err) {
        return refused(err);
      }
      answered();
      if (id !== openId) moved = {};
      openId = id;
      shown = answer;
      saved = arrangement.positions;
      versions = null;
      markOpen();
      draw();
      showHistory();
    },
    /** a step's fields and stored text in the left column (REQ-GA-036, 037); a missing step names only its kind */
    async selectStep(id) {
      const step = shown?.graph.nodes.find((n) => n.id === id);
      const node = picture?.nodes.find((n) => n.id === id);
      if (!node) return controller.selectNothing();
      const kind = step ? kindOf(step, isWorkflow(shown.graph)).kind : node.kind;
      showSelection(`step ${id}`, stepFields(step ?? { id }, kind, isWorkflow(shown.graph) ? shown.steps?.[id] : null), step ?? { id, missing: true });
    },
    /** a connection's ends, role and stored text in the left column (REQ-GA-036) */
    async selectConnection(id) {
      const edge = shown?.graph.edges.find((e) => e.id === id);
      if (!edge) return controller.selectNothing();
      showSelection(`connection ${id}`, connectionFields(edge), edge);
    },
    /** nothing selected leaves the left column without fields (REQ-GA-044) */
    async selectNothing() {
      selection.replaceChildren(hint);
    },
    /** the versions of the open graph, newest first (REQ-GA-038) */
    async openHistory() {
      if (openId === null) return;
      try {
        versions = await api.versions(openId);
      } catch (err) {
        return refused(err);
      }
      answered();
      showHistory();
    },
    /** an earlier (or the current) version, drawn read-only and named in the status bar (REQ-GA-039) */
    async showVersion(version) {
      let answer;
      try {
        answer = await api.readGraph(openId, version);
      } catch (err) {
        return refused(err);
      }
      answered();
      shown = answer;
      draw();
      showHistory();
    },
    /** one version older or newer; nothing beyond the ends (REQ-GA-040) */
    async previous() { return step('previous'); },
    async next() { return step('next'); },
    /** the connection style and the automatic arrangement, at once and without reading the graph again; kept on the device (REQ-GA-034, 035) */
    async setSettings(change) {
      settings = { ...settings, ...validSettings(change) };
      saveSettings(storage, settings);
      showSettings();
      const { edges, physics } = drawingOptions(settings);
      drawing?.setOptions({ edges, physics });
    },
    /** the layered reset: every connection points forward; the moved places are let go (REQ-GA-033) */
    async layered() {
      if (!picture) return;
      moved = {};
      theDrawing().show({ nodes: layered(picture.nodes, picture.edges), edges: picture.edges }, drawingOptions(settings, 'layered'));
    },
  };
  async function step(direction) {
    const version = versions && shown ? neighbour(versions, shown.version, direction) : null;
    if (version !== null) await controller.showVersion(version);
  }

  return controller;
}
