// Keyboard use and screen readers (ui/REQUIREMENTS_CHAT.md 9).
//  - announce(): one polite live region for finished messages (the list itself is not live: streamed text would be read token by token)
//  - shortcuts: "/" the composer, Alt+ArrowDown the latest message, Alt+C show or hide the chat, Alt+M the menu
import { captionText } from './chat-model.js';

export function isTypingTarget(target) {
  if (!target || !target.tagName) return false;
  const tag = target.tagName.toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select' || target.isContentEditable === true;
}

/** which action a key press means (pure, tested): returns null when it is not a shortcut */
export function shortcutFor(event, typing = false) {
  if (event.ctrlKey || event.metaKey) return null;
  if (event.altKey) {
    if (event.key === 'ArrowDown') return 'latest';
    if (event.key.toLowerCase() === 'c') return 'toggle';
    if (event.key.toLowerCase() === 'm') return 'menu';
    return null;
  }
  if (event.key === '/' && !typing) return 'composer';
  return null;
}

export function initAnnouncements({ region, socket, list, t }) {
  let timer = 0;

  function say(text) {
    window.clearTimeout(timer);
    region.textContent = '';
    // a short pause so that the same text is announced again
    timer = window.setTimeout(() => { region.textContent = text; }, 50);
  }

  socket.on('chat_start', () => list.setAttribute('aria-busy', 'true'));
  socket.on('chat_done', (data) => {
    list.setAttribute('aria-busy', 'false');
    if (data.text) say(`${t('app.title')}: ${captionText(data.text, 300)}`);
  });
  socket.on('chat_message', (message) => {
    if (message.role === 'system' || (message.role === 'assistant' && message.auto)) say(captionText(message.text, 300));
  });
  return { say };
}

export function initShortcuts({ composer, layout, menu, chat, win = window }) {
  win.addEventListener('keydown', (event) => {
    if (event.defaultPrevented || document.querySelector('dialog[open]')) return;
    const action = shortcutFor(event, isTypingTarget(event.target));
    if (!action) return;
    event.preventDefault();
    if (action === 'composer') {
      if (layout.collapsed) layout.setCollapsed(false);
      composer.focus();
    } else if (action === 'latest') {
      chat.scrollDown();
    } else if (action === 'toggle') {
      layout.setCollapsed(!layout.collapsed);
    } else if (action === 'menu') {
      if (layout.collapsed) layout.setCollapsed(false);
      menu.open();
    }
  });
}
