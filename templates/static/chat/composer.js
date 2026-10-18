// The input field: grows up to 8 lines, Enter sends (Shift+Enter = new line; on touch devices Enter is a new line
// and the send button sends), the draft survives a reload.

export const MAX_LENGTH = 8000;

/** trim, cut to the limit, drop control characters (but keep line breaks and tabs) */
export function normalizeMessage(text) {
  return String(text ?? '')
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '')
    .trim()
    .slice(0, MAX_LENGTH);
}

export function initComposer({ form, input, send, storage, suggestions, onSend, win = window }) {
  const coarse = () => win.matchMedia?.('(pointer: coarse)').matches ?? false;
  let composing = false;

  function grow() {
    input.style.height = 'auto';
    const style = win.getComputedStyle(input);
    const line = parseFloat(style.lineHeight) || 22;
    const frame = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom) + parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
    input.style.height = `${Math.min(input.scrollHeight + parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth), line * 8 + frame)}px`;
  }

  function refresh() {
    send.disabled = normalizeMessage(input.value) === '';
    storage.set('mia.draft', input.value);
    grow();
  }

  function submit() {
    const text = normalizeMessage(input.value);
    if (!text) return;
    if (onSend(text) === false) return;
    input.value = '';
    storage.remove('mia.draft');
    refresh();
  }

  input.value = storage.get('mia.draft', '') ?? '';
  input.addEventListener('input', refresh);
  input.addEventListener('compositionstart', () => { composing = true; });
  input.addEventListener('compositionend', () => { composing = false; });
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && !composing && !coarse()) {
      event.preventDefault();
      submit();
    }
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    submit();
  });
  for (const suggestion of suggestions) {
    suggestion.addEventListener('click', () => {
      input.value = suggestion.dataset.text ?? suggestion.textContent;
      refresh();
      input.focus();
    });
  }

  refresh();
  return { focus: () => input.focus(), refresh };
}
