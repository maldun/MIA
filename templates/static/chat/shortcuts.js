// Keyboard shortcuts of the chat page. Esc closes layers (menu, dialogs: handled where they live).
//   /          focus the message field        (when no text field has the focus)
//   Alt+H      hide or show the chat
//   Alt+End    scroll to the latest message
//   Alt+M      open the menu
//   Alt+,      open the settings
//   ?          list the shortcuts

export const SHORTCUTS = [
  { keys: '/', action: 'focus', label: 'shortcuts.focus' },
  { keys: 'Alt+H', action: 'collapse', label: 'shortcuts.collapse' },
  { keys: 'Alt+End', action: 'latest', label: 'shortcuts.latest' },
  { keys: 'Alt+M', action: 'menu', label: 'shortcuts.menu' },
  { keys: 'Alt+,', action: 'settings', label: 'shortcuts.settings' },
  { keys: '?', action: 'help', label: 'shortcuts.help' },
];

export function isTyping(target) {
  const tag = target?.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || Boolean(target?.isContentEditable);
}

/** the action for a key event, or null (pure, for tests) */
export function actionFor(event) {
  if (event.ctrlKey || event.metaKey) return null;
  if (event.altKey) {
    const key = String(event.key).toLowerCase();
    if (key === 'h') return 'collapse';
    if (key === 'end') return 'latest';
    if (key === 'm') return 'menu';
    if (key === ',') return 'settings';
    return null;
  }
  if (isTyping(event.target)) return null;
  if (event.key === '/') return 'focus';
  if (event.key === '?') return 'help';
  return null;
}

export function initShortcuts({ actions, doc = document }) {
  doc.addEventListener('keydown', (event) => {
    if (event.defaultPrevented || event.isComposing) return;
    if (doc.querySelector('dialog[open]')) return;
    const action = actionFor(event);
    if (!action || !actions[action]) return;
    event.preventDefault();
    actions[action]();
  });
}
