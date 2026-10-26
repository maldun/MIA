// The workspace dialog (REQ-CLV-009 to -012): the records of tasks, memos and memory, the trust of sources, the persona and the score.
// Everything is shared by all users (CON-6). A change by another user arrives as an event (item_changed, trust_changed, persona_changed, score) and the
// open tab is drawn again, unless the reader is typing in it: then a short note says so and nothing is overwritten.
import { itemDraftError, parseTrust, scoreLines } from './panels-model.js';

const TABS = ['tasks', 'memos', 'memory', 'trust', 'persona', 'score'];
const RECORD_TABS = ['tasks', 'memos', 'memory'];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function initWorkspace({ dialog, tabsEl, body, closeButton, api, socket, t, notify = () => {} }) {
  let active = 'tasks';

  function field(labelKey, control) {
    const label = el('label', 'setting');
    label.append(el('span', '', t(labelKey)), control);
    return label;
  }

  function input(value = '', type = 'text') {
    const node = el('input');
    node.type = type;
    node.value = value;
    return node;
  }

  async function run(action, doneKey) {
    try {
      await action();
      if (doneKey) notify(t(doneKey));
      return true;
    } catch (error) {
      notify(error.status === 0 ? t('chat.offline') : error.rule === 'source' ? t('workspace.need_source') : t('workspace.failed'));
      return false;
    }
  }

  // --- tasks, memos, memory --------------------------------------------------------------------
  async function drawRecords(kind, target) {
    const items = await api.items(kind);
    const add = el('form', 'workspace-add');
    const text = input('', 'text');
    text.setAttribute('aria-label', t(`workspace.tab.${kind}`));
    text.placeholder = t(`workspace.new.${kind}`);
    const source = kind === 'memory' ? input('', 'text') : null;
    if (source) source.placeholder = t('workspace.source');
    const addButton = el('button', '', t('workspace.add'));
    addButton.type = 'submit';
    add.append(text, ...(source ? [source] : []), addButton);
    add.addEventListener('submit', async (event) => {
      event.preventDefault();
      const problem = itemDraftError(kind, text.value, source?.value);
      if (problem) { notify(t(problem === 'source' ? 'workspace.need_source' : 'workspace.need_text')); return; }
      if (await run(() => api.saveItem(kind, null, text.value, source?.value || null), 'workspace.saved')) show(kind);
    });
    const list = el('ul', 'workspace-list');
    list.setAttribute('aria-label', t(`workspace.tab.${kind}`));
    for (const item of items) {
      const row = el('li');
      const edit = input(item.text, 'text');
      edit.setAttribute('aria-label', t(`workspace.tab.${kind}`));
      const meta = el('small', 'hint', item.source ? `${item.author} · ${item.source}` : item.author);
      const save = el('button', '', t('workspace.save'));
      save.type = 'button';
      save.addEventListener('click', async () => {
        const problem = itemDraftError(kind, edit.value, item.source);
        if (problem) { notify(t('workspace.need_text')); return; }
        if (await run(() => api.saveItem(kind, item.id, edit.value, item.source ?? null), 'workspace.saved')) show(kind);
      });
      const remove = el('button', '', t('workspace.delete'));
      remove.type = 'button';
      remove.addEventListener('click', async () => {
        if (await run(() => api.deleteItem(kind, item.id), 'workspace.deleted')) show(kind);
      });
      row.append(edit, meta, save, remove);
      list.append(row);
    }
    if (!items.length) list.append(el('li', 'hint', t('workspace.empty')));
    target.append(add, list);
  }

  // --- trust of sources ----------------------------------------------------------------------------
  async function drawTrust(target) {
    const trust = await api.trust();
    const list = el('ul', 'workspace-list');
    list.setAttribute('aria-label', t('workspace.tab.trust'));
    for (const [source, value] of Object.entries(trust)) {
      const row = el('li');
      const edit = input(String(value), 'text');
      edit.inputMode = 'decimal';
      edit.setAttribute('aria-label', source);
      const save = el('button', '', t('workspace.save'));
      save.type = 'button';
      save.addEventListener('click', async () => {
        const parsed = parseTrust(edit.value);
        if (parsed === null) { notify(t('workspace.trust_range')); return; }
        if (await run(() => api.setTrust(source, parsed), 'workspace.saved')) show('trust');
      });
      row.append(el('span', 'source', source), edit, save);
      list.append(row);
    }
    target.append(el('p', 'hint', t('workspace.trust_hint')), list);
  }

  // --- persona ---------------------------------------------------------------------------------------
  async function drawPersona(target) {
    const persona = await api.persona();
    const area = el('textarea');
    area.rows = 8;
    area.value = persona.text ?? '';
    area.setAttribute('aria-label', t('workspace.tab.persona'));
    const save = el('button', '', t('workspace.save'));
    save.type = 'button';
    save.addEventListener('click', async () => {
      if (!area.value.trim()) { notify(t('workspace.need_text')); return; }
      if (await run(() => api.savePersona({ ...persona, text: area.value }), 'workspace.saved')) show('persona');
    });
    target.append(el('p', 'hint', t('workspace.persona_hint')), area, save);
  }

  // --- score -----------------------------------------------------------------------------------------
  async function drawScore(target) {
    const lines = scoreLines(await api.score(), t);
    const list = el('ul', 'workspace-list score');
    list.setAttribute('aria-label', t('workspace.tab.score'));
    for (const line of lines) {
      const row = el('li', line.key === 'overall' ? 'overall' : '');
      row.append(el('span', '', line.label), el('strong', '', (line.value > 0 ? '+' : '') + line.value));
      list.append(row);
    }
    target.append(list);
  }

  const DRAW = { tasks: (target) => drawRecords('tasks', target), memos: (target) => drawRecords('memos', target), memory: (target) => drawRecords('memory', target), trust: drawTrust, persona: drawPersona, score: drawScore };

  function drawTabs() {
    tabsEl.textContent = '';
    for (const tab of TABS) {
      const button = el('button', 'tab', t(`workspace.tab.${tab}`));
      button.type = 'button';
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-selected', String(tab === active));
      button.addEventListener('click', () => show(tab));
      tabsEl.append(button);
    }
  }

  // Several drawings can run at once (a save redraws the tab and so does the event of the change). Each draws into its own holder and only the
  // latest one is put on the page, so a record is never listed twice.
  let drawing = 0;
  async function show(tab) {
    active = tab;
    drawTabs();
    const mine = ++drawing;
    const holder = document.createElement('div');
    body.setAttribute('aria-busy', 'true');
    try {
      await DRAW[tab](holder);
    } catch (error) {
      holder.textContent = t(error.status === 0 ? 'chat.offline' : 'workspace.failed');
    }
    if (mine !== drawing) return;
    body.replaceChildren(...holder.childNodes);
    body.setAttribute('aria-busy', 'false');
  }

  /** a change by another user: draw the open tab again, unless the reader is typing in it */
  function changedElsewhere(tabs) {
    if (!dialog.open || !tabs.includes(active)) return;
    const typing = body.contains(document.activeElement) && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
    if (typing) notify(t('workspace.changed_elsewhere'));
    else show(active);
  }
  socket.on('item_changed', (event) => changedElsewhere([event?.kind]));
  socket.on('trust_changed', () => changedElsewhere(['trust']));
  socket.on('persona_changed', () => changedElsewhere(['persona']));
  socket.on('score', () => changedElsewhere(['score']));

  closeButton.addEventListener('click', () => dialog.close());
  return {
    open(tab = active) {
      if (!dialog.open) dialog.showModal();
      return show(RECORD_TABS.includes(tab) || TABS.includes(tab) ? tab : 'tasks');
    },
  };
}
