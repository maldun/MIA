// The input field: grows up to 8 lines, Enter sends (Shift+Enter = new line; on touch devices Enter is a new line
// and the send button sends), the draft survives a reload, ArrowUp in an empty field recalls the last message.
// While MIA answers a stop button appears next to the send button (the next message waits in the queue).

export const MAX_LENGTH = 8000;
const COUNTER_FROM = 7000;

/** trim, cut to the limit, drop control characters (but keep line breaks and tabs) */
export function normalizeMessage(text) {
  return String(text ?? '')
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '')
    .trim()
    .slice(0, MAX_LENGTH);
}

export function initComposer({ form, input, send, stop, counter, storage, suggestions, onSend, onStop, sendOnEnter = () => true, win = window }) {
  const coarse = () => win.matchMedia?.('(pointer: coarse)').matches ?? false;
  let composing = false;
  let online = true;
  let busy = false;
  let last = storage.get('mia.last', '') ?? '';

  function grow() {
    input.style.height = 'auto';
    const style = win.getComputedStyle(input);
    const line = parseFloat(style.lineHeight) || 22;
    const border = parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
    const frame = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom) + border;
    input.style.height = `${Math.min(input.scrollHeight + border, line * 8 + frame)}px`;
  }

  function refresh() {
    send.disabled = !online || normalizeMessage(input.value) === '';
    stop.hidden = !busy;
    const length = input.value.length;
    counter.hidden = length < COUNTER_FROM;
    counter.textContent = `${length} / ${MAX_LENGTH}`;
    storage.set('mia.draft', input.value);
    grow();
  }

  async function submit() {
    const text = normalizeMessage(input.value);
    if (!text || !online) return;
    if ((await onSend(text)) === false) return;
    last = text;
    storage.set('mia.last', last);
    input.value = '';
    storage.remove('mia.draft');
    refresh();
  }

  input.value = storage.get('mia.draft', '') ?? '';
  input.addEventListener('input', refresh);
  input.addEventListener('compositionstart', () => { composing = true; });
  input.addEventListener('compositionend', () => { composing = false; });
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && !composing && !coarse() && sendOnEnter()) {
      event.preventDefault();
      submit();
    } else if (event.key === 'ArrowUp' && input.value === '' && last) {
      input.value = last;
      refresh();
      event.preventDefault();
    }
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    submit();
  });
  stop.addEventListener('click', () => onStop());
  for (const suggestion of suggestions) {
    suggestion.addEventListener('click', () => {
      input.value = suggestion.dataset.text ?? suggestion.textContent;
      refresh();
      input.focus();
    });
  }

  refresh();
  if (!coarse() && win.innerWidth >= 600) input.focus();      // no keyboard popping up on phones
  return {
    focus: () => input.focus(),
    refresh,
    fill(text) {
      input.value = text;
      refresh();
      input.focus();
    },
    setOnline(value) {
      online = value;
      refresh();
    },
    setBusy(value) {
      busy = value;
      refresh();
    },
  };
}
