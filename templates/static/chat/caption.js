// Caption mode: while the chat is collapsed, MIA's current answer appears at the bottom of the character area
// and fades out a few seconds after she has finished. The text is plain (no markdown), the end of a long answer.
import { captionText } from './chat-model.js';

const MIN_MS = 4000;
const PER_CHARACTER_MS = 60;

export function initCaption({ el, socket, isCollapsed, win = window }) {
  let timer = 0;

  function hide() {
    win.clearTimeout(timer);
    el.classList.remove('visible');
  }

  function show(text, final) {
    if (!isCollapsed()) return;
    const line = captionText(text);
    if (!line) return;
    el.textContent = line;
    el.classList.add('visible');
    win.clearTimeout(timer);
    // while she is still writing the caption stays; after the end it is readable for a while, then it goes
    timer = win.setTimeout(hide, final ? Math.max(MIN_MS, line.length * PER_CHARACTER_MS) : 12000);
  }

  socket.on('chat_delta', (data) => show(data.text, false));
  socket.on('chat_done', (data) => (data.text ? show(data.text, true) : hide()));
  socket.on('chat_message', (message) => {
    if (message.role === 'assistant' && message.auto) show(message.text, true);
  });

  return { hide, update: () => { if (!isCollapsed()) hide(); } };
}
