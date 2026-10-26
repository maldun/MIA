// The conversation on the page: history, live messages (chat_* events), streaming, sending with retry, paging, autoscroll.
// The server is the source of truth (see ui/README.md, chat backend); this module only draws it.
import { lastAnswerId, voteArgs } from './panels-model.js';
import { clock, continuesGroup, dayKey, dayLabel, emojiFor, linkify, pipelineHeadline, pipelineLine, pipelineRows, pipelineState, queueText, relativeTime, senderName, trimOldest, upsert, MAX_IN_DOM } from './chat-model.js';

export function isNearBottom(element, threshold = 80) {
  return element.scrollHeight - element.scrollTop - element.clientHeight <= threshold;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/**
 * me(): the account of this page (null when not known); onLoginRequired(): the server says there is no session (IF-101: 401 unauthenticated);
 * api: the REST calls of IF-101 v1 (api.js) for the actions under an answer: speak again, plus and minus, how I got there, regenerate.
 */
export function initChat({ list, empty, jump, olderButton, socket, render, t, origin = location.origin, win = window, notify = () => {}, me = () => null, onLoginRequired = () => {}, api = null }) {
  const messages = [];          // sorted by id, what is in the DOM
  const rows = new Map();       // id -> row element
  const pendingText = new Map();
  const unsent = new Map();     // client id -> text of messages that could not be sent
  let hasOlder = false;
  let loading = false;
  let stick = true;
  let unread = 0;
  let frame = 0;

  // --- drawing ---------------------------------------------------------------------------------
  function bubbleContent(bubble, message) {
    bubble.textContent = '';
    if (message.role === 'user') {
      for (const part of linkify(message.text)) {
        if (part.href) {
          const a = el('a', null, part.href);
          a.href = part.href;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          bubble.append(a);
        } else {
          bubble.append(document.createTextNode(part.text));
        }
      }
    } else if (message.role === 'assistant') {
      if (message.streaming && !message.text) {
        bubble.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
      } else {
        bubble.classList.add('md');
        bubble.innerHTML = render(message.text);
      }
    } else {
      bubble.textContent = message.text;
    }
  }

  function buildRow(message, previous) {
    const row = el('div', `row ${message.role}`);
    row.dataset.id = message.id;
    if (message.role === 'system') {
      row.append(el('div', 'msg note', message.text));
      return row;
    }
    if (!continuesGroup(previous, message)) {
      const head = el('div', 'msg-head');
      head.append(el('span', 'msg-name', senderName(message, me(), t)));
      if (message.role === 'assistant') {
        const badge = el('span', 'badge');
        badge.dataset.role = 'badge';
        head.append(badge);
        if (message.auto) head.append(el('span', 'tag', t('chat.automatic')));
      }
      row.append(head);
    }
    if (message.role === 'assistant') {
      const steps = el('details', 'pipeline');
      steps.dataset.role = 'pipeline';
      steps.hidden = true;
      steps.append(el('summary'), el('ol', 'pipeline-steps'));
      steps.querySelector('summary').addEventListener('click', () => { steps.dataset.touched = '1'; });
      row.append(steps);
    }
    const bubble = el('div', `msg ${message.role}`);
    bubble.dataset.role = 'bubble';
    row.append(bubble);
    const foot = el('div', 'msg-foot');
    const time = el('time');
    time.dataset.role = 'time';
    foot.append(time);
    const state = el('span', 'state');
    state.dataset.role = 'state';
    foot.append(state);
    if (message.role === 'assistant') {
      const copy = el('button', 'link-button', t('chat.copy'));
      copy.type = 'button';
      copy.dataset.action = 'copy';
      foot.append(copy);
      if (api) {
        for (const [action, shown, label] of [['speak', '🔊', 'chat.speak'], ['up', '👍', 'chat.plus'], ['down', '👎', 'chat.minus'], ['how', 'ⓘ', 'chat.how'], ['regenerate', '↻', 'chat.regenerate']]) {
          const button = el('button', 'link-button action', shown);
          button.type = 'button';
          button.dataset.action = action;
          button.title = t(label);
          button.setAttribute('aria-label', t(label));
          button.hidden = true;                    // shown by fill() once the answer is written, "regenerate" only on the last one
          foot.append(button);
        }
      }
    }
    row.append(foot);
    return row;
  }

  /** the expandable block "how I got there": open while the answer is made, closed afterwards (unless the reader opened or closed it) */
  function drawPipeline(row, message) {
    const steps = row.querySelector('[data-role=pipeline]');
    if (!steps) return;
    const events = message.pipeline ?? [];
    steps.hidden = events.length === 0;
    if (!events.length) return;
    const state = pipelineState(events);
    steps.classList.toggle('running', !state.finished);
    steps.classList.toggle('failed', state.finished && state.status !== 'done');
    steps.querySelector('summary').textContent = pipelineHeadline(events, t);
    const list = steps.querySelector('ol');
    list.textContent = '';
    for (const step of pipelineRows(events)) {
      const item = el('li', `step ${step.state}`, pipelineLine(step));
      if (step.item !== null) item.dataset.item = step.item;
      list.append(item);
    }
    if (!steps.dataset.touched) steps.open = !state.finished && Boolean(message.streaming);
  }

  function fill(row, message) {
    const bubble = row.querySelector('[data-role=bubble]');
    if (bubble) {
      bubble.classList.toggle('stopped', message.status === 'stopped');
      bubbleContent(bubble, message);
      bubble.hidden = message.role === 'assistant' && !message.streaming && !message.text;      // nothing came before the error
    }
    drawPipeline(row, message);
    const copy = row.querySelector('[data-action=copy]');
    if (copy) copy.hidden = !message.text;
    for (const action of ['speak', 'up', 'down', 'how']) {
      const button = row.querySelector(`[data-action=${action}]`);
      if (button) button.hidden = !message.text || Boolean(message.streaming) || String(message.id).startsWith('~');
    }
    const badge = row.querySelector('[data-role=badge]');
    if (badge) {
      badge.textContent = emojiFor(message.emotion);
      badge.title = message.emotion ?? '';
      badge.hidden = !message.emotion;
    }
    const time = row.querySelector('[data-role=time]');
    if (time && message.created) {
      time.dateTime = message.created;
      time.textContent = relativeTime(message.created, Date.now(), t);
      time.title = new Date(message.created).toLocaleString();
    }
    const state = row.querySelector('[data-role=state]');
    if (state) {
      let text = '';
      if (message.local === 'sending') text = t('chat.sending');
      else if (message.local === 'queued') text = queueText(message, t);
      else if (message.status === 'stopped') text = t('chat.stopped');
      else if (message.status === 'error') text = t('chat.error');
      state.textContent = text;
    }
    const foot = row.querySelector('.msg-foot');
    const retry = row.querySelector('[data-action=retry]');
    if (message.local === 'failed' && !retry && foot) {
      const button = el('button', 'link-button danger', t('chat.retry'));
      button.type = 'button';
      button.dataset.action = 'retry';
      foot.append(button);
      state.textContent = t('chat.failed');
    } else if (message.local !== 'failed' && retry) {
      retry.remove();
    }
    row.classList.toggle('local', Boolean(message.local));
  }

  function separatorBefore(row) {
    const sibling = row?.previousElementSibling;
    return sibling?.classList.contains('day') ? sibling : null;
  }

  // a day separator stands in front of the first message of each day
  function ensureSeparator(index) {
    const message = messages[index];
    const row = rows.get(message?.id);
    if (!row) return;
    const previous = messages[index - 1];
    const needed = !previous || dayKey(previous.created) !== dayKey(message.created);
    const present = separatorBefore(row);
    if (needed && !present) {
      const separator = el('div', 'day', dayLabel(message.created, Date.now(), t));
      list.insertBefore(separator, row);
    } else if (!needed && present) {
      present.remove();
    }
  }

  function place(message) {
    const index = upsert(messages, message);
    const stored = messages[index];
    let row = rows.get(stored.id);
    if (!row && stored.client_id) {
      row = [...rows.values()].find((r) => r.dataset.client === stored.client_id);
      if (row) {
        rows.delete(row.dataset.id);
        row.dataset.id = stored.id;
        rows.set(stored.id, row);
      }
    }
    if (!row) {
      row = buildRow(stored, messages[index - 1]);
      if (stored.client_id) row.dataset.client = stored.client_id;
      rows.set(stored.id, row);
      const nextRow = messages[index + 1] ? rows.get(messages[index + 1].id) : null;
      list.insertBefore(row, nextRow ? (separatorBefore(nextRow) ?? nextRow) : null);
      ensureSeparator(index);
      if (messages[index + 1]) ensureSeparator(index + 1);
    }
    fill(row, stored);
    refreshRegenerate();
    return stored;
  }

  // "regenerate" is offered on the last answer only (IF-101: not_the_last_answer is refused)
  let regenerateId = null;
  function showRegenerate(id, visible) {
    const button = id ? rows.get(id)?.querySelector('[data-action=regenerate]') : null;
    if (button) button.hidden = !visible;
  }
  function refreshRegenerate() {
    if (!api) return;
    const last = lastAnswerId(messages);
    if (regenerateId !== last) showRegenerate(regenerateId, false);
    showRegenerate(last, true);
    regenerateId = last;
  }

  function afterAdd(message, fromServer) {
    empty.hidden = true;
    if (stick) {
      win.requestAnimationFrame(scrollDown);
    } else if (fromServer && message.role !== 'user') {
      unread += 1;
      showJump();
    }
    const removed = trimOldest(messages, MAX_IN_DOM);
    for (const gone of removed) {
      const row = rows.get(gone.id);
      const before = row?.previousElementSibling;
      row?.remove();
      rows.delete(gone.id);
      if (before?.classList.contains('day') && !before.nextElementSibling?.classList.contains('row')) before.remove();
      hasOlder = true;
    }
    if (removed.length) olderButton.hidden = false;
  }

  // --- scrolling -------------------------------------------------------------------------------
  let lastTop = 0;

  function scrollDown() {
    list.scrollTo({ top: list.scrollHeight, behavior: 'instant' });      // never animated through the top (that would page back)
    lastTop = list.scrollTop;
    unread = 0;
    jump.hidden = true;
  }

  function showJump() {
    jump.hidden = false;
    jump.textContent = unread > 0 ? t('messages.jump_count', { n: unread }) : t('messages.jump');
  }

  list.addEventListener('scroll', () => {
    stick = isNearBottom(list);
    if (stick) {
      unread = 0;
      jump.hidden = true;
    }
    const upward = list.scrollTop < lastTop;
    lastTop = list.scrollTop;
    if (upward && list.scrollTop < 60 && hasOlder && !loading) loadOlder();
  });
  jump.addEventListener('click', () => {
    stick = true;
    scrollDown();
  });

  // --- history ---------------------------------------------------------------------------------
  async function fetchPage(before) {
    const url = new URL('/api/chat/history', origin);
    url.searchParams.set('limit', '50');
    if (before) url.searchParams.set('before', before);
    const response = await fetch(url, { credentials: 'same-origin' });
    if (response.status === 401) {                  // no session: the login asks, then the page reloads
      onLoginRequired();
      return { messages: [], older: false };
    }
    if (!response.ok) throw new Error(`history ${response.status}`);
    return response.json();
  }

  let initial = true;

  async function loadLatest() {
    try {
      const page = await fetchPage();
      for (const message of page.messages) place({ ...message, local: undefined });
      if (initial) hasOlder = page.older;
      initial = false;
      olderButton.hidden = !hasOlder;
      if (page.messages.length) {
        empty.hidden = true;
        if (stick) scrollDown();      // at once: a reader at the top would page back through the whole history
      }
    } catch (error) {
      notify(t('chat.history_failed'));
    }
  }

  async function loadOlder() {
    if (loading || !messages.length) return;
    loading = true;
    try {
      const before = messages.find((m) => !m.local)?.id;
      const page = await fetchPage(before);
      const height = list.scrollHeight;
      const top = list.scrollTop;
      for (const message of page.messages) place(message);
      hasOlder = page.older;
      olderButton.hidden = !hasOlder;
      list.scrollTop = top + (list.scrollHeight - height);   // the reader stays where he was
    } catch (error) {
      notify(t('chat.history_failed'));
    } finally {
      loading = false;
    }
  }
  olderButton.addEventListener('click', loadOlder);

  // --- live events -----------------------------------------------------------------------------
  function flush() {
    frame = 0;
    for (const [id, text] of pendingText) {
      const message = messages.find((m) => m.id === id);
      const row = rows.get(id);
      if (message && row) {
        message.text = text;
        fill(row, message);
      }
    }
    pendingText.clear();
    if (stick) scrollDown();
  }

  function streaming(id) {
    let message = messages.find((m) => m.id === id);
    if (!message) {
      message = place({ id, role: 'assistant', text: '', streaming: true, created: new Date().toISOString(), status: 'done' });
      afterAdd(message, true);
    }
    return message;
  }

  socket.on('chat_message', (message) => {
    const placed = place({ ...message, local: undefined });
    afterAdd(placed, true);
  });
  socket.on('chat_start', (data) => {
    for (const m of messages) if (m.local === 'queued') place({ id: m.id, local: undefined });
    const placed = place({ id: data.id, role: 'assistant', text: '', streaming: true, created: data.created, status: 'done' });
    afterAdd(placed, true);
  });
  socket.on('chat_delta', (data) => {
    streaming(data.id);
    pendingText.set(data.id, data.text);
    if (!frame) frame = win.requestAnimationFrame(flush);
  });
  socket.on('chat_pipeline', (data) => {
    const message = streaming(data.id);
    (message.pipeline ??= []).push(data.event);
    const row = rows.get(data.id);
    if (row) drawPipeline(row, message);
    if (stick) win.requestAnimationFrame(scrollDown);
  });
  socket.on('chat_done', (data) => {
    streaming(data.id);
    pendingText.delete(data.id);
    const placed = place({ id: data.id, text: data.text, emotion: data.emotion, status: data.status, streaming: false });
    if (stick) win.requestAnimationFrame(scrollDown);
    return placed;
  });
  socket.on('chat_error', (data) => notify(data?.message ?? t('chat.error')));

  // --- sending ---------------------------------------------------------------------------------
  function newClientId() {
    return globalThis.crypto?.randomUUID?.() ?? `c${Date.now()}${Math.random().toString(16).slice(2)}`;
  }

  function transmit(clientId, text, command) {
    socket.timeout(10000).emit('chat_send', { id: clientId, text }, (error, ack) => {
      const row = [...rows.values()].find((r) => r.dataset.client === clientId);
      const message = row ? messages.find((m) => m.id === row.dataset.id) : null;
      // today's server answers {ok, message, queued}; IF-101 answers {id, position} (the mock server adds ok and message)
      const accepted = ack?.ok ?? (ack?.id !== undefined);
      if (error || !accepted) {
        if (message) place({ id: message.id, local: 'failed' });
        unsent.set(clientId, text);
        notify(ack?.error ?? t('chat.sending_failed'));
        return;
      }
      unsent.delete(clientId);
      const waiting = ack.queued ?? (ack.position >= 1);
      if (message && ack.message) place({ ...ack.message, client_id: clientId, local: waiting ? 'queued' : undefined, position: ack.position });
    });
  }

  function send(text) {
    const clientId = newClientId();
    const command = text.trim().startsWith('/') && text.trim().endsWith('!');
    if (!command) {
      const placed = place({ id: `~${Date.now()}-${clientId}`, client_id: clientId, role: 'user', text, created: new Date().toISOString(), status: 'done', local: 'sending' });
      stick = true;
      afterAdd(placed, false);
    }
    transmit(clientId, text, command);
  }

  /** the actions under an answer (IF-101 v1); a refused call is told in plain words */
  async function answerAction(button, row, message) {
    const action = button.dataset.action;
    try {
      if (action === 'speak') {
        await api.speakAgain(message.id);
      } else if (action === 'up' || action === 'down') {
        const vote = voteArgs(message, action === 'up' ? 1 : -1);
        const result = await api.vote(vote.subject, vote.category, vote.value);
        for (const other of row.querySelectorAll('[data-action=up],[data-action=down]')) other.setAttribute('aria-pressed', String(other === button));
        notify(t('vote.thanks', { n: result.score?.overall ?? 0 }));
      } else if (action === 'regenerate') {
        await api.regenerate(message.id);
        notify(t('chat.regenerating'));
      } else if (action === 'how') {
        await toggleAccount(row, message);
      }
    } catch (error) {
      notify(error.code === 'queue_full' ? t('chat.queue_full') : error.status === 0 ? t('chat.offline') : t('chat.action_failed'));
    }
  }

  /** the step-by-step account of an answer, written by the Backend in plain sentences */
  async function toggleAccount(row, message) {
    let block = row.querySelector('.account');
    if (block) {
      block.hidden = !block.hidden;
      return;
    }
    const lines = await api.account(message.id);
    block = el('ol', 'account');
    block.setAttribute('aria-label', t('chat.how'));
    for (const line of lines) block.append(el('li', '', line.plain));
    if (!lines.length) block.append(el('li', '', t('chat.how_empty')));
    row.querySelector('.msg-foot').before(block);
  }

  list.addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const row = button.closest('.row');
    const message = messages.find((m) => m.id === row.dataset.id);
    if (button.dataset.action === 'copy' && message) {
      try {
        await navigator.clipboard.writeText(message.text);
        button.textContent = t('chat.copied');
        win.setTimeout(() => { button.textContent = t('chat.copy'); }, 1500);
      } catch (error) {
        notify(t('chat.copy_failed'));
      }
    }
    if (api && message && ['speak', 'up', 'down', 'how', 'regenerate'].includes(button.dataset.action)) await answerAction(button, row, message);
    if (button.dataset.action === 'retry' && message) {
      place({ id: message.id, local: 'sending' });
      transmit(row.dataset.client, message.text, false);
    }
  });

  // times in the bubbles are relative: refresh them once a minute
  win.setInterval(() => {
    for (const message of messages) {
      const row = rows.get(message.id);
      const time = row?.querySelector('[data-role=time]');
      if (time && message.created) time.textContent = relativeTime(message.created, Date.now(), t);
    }
  }, 60000);

  /** a short note that is not part of the conversation (errors, hints); it is not stored */
  function note(text) {
    const row = el('div', 'row system');
    row.append(el('div', 'msg note', text));
    list.append(row);
    empty.hidden = true;
    if (stick) win.requestAnimationFrame(scrollDown);
  }

  return { loadLatest, loadOlder, send, note, scrollDown, messages, rows };
}
