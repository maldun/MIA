// Slash commands: typing "/" shows the list (from /api/chat/commands, the same list the server uses), filtered while
// typing; arrows / Enter / Tab / tap pick one, Escape closes. The pure filter is in chat-model.js.
import { filterCommands } from './chat-model.js';

export async function loadCommands(origin = location.origin) {
  try {
    const response = await fetch(new URL('/api/chat/commands', origin));
    return response.ok ? (await response.json()).commands : [];
  } catch (error) {
    return [];
  }
}

export function initPalette({ input, list, commands, onPick }) {
  let items = [];
  let active = 0;

  function close() {
    items = [];
    list.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }

  function draw() {
    list.textContent = '';
    items.forEach((command, index) => {
      const item = document.createElement('li');
      item.id = `palette-${index}`;
      item.setAttribute('role', 'option');
      item.setAttribute('aria-selected', String(index === active));
      const name = document.createElement('span');
      name.className = 'command';
      name.textContent = command.command;
      const description = document.createElement('span');
      description.className = 'description';
      description.textContent = command.description;
      item.append(name, description);
      item.addEventListener('pointerdown', (event) => {
        event.preventDefault();      // the input keeps the focus
        pick(command);
      });
      list.append(item);
    });
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    input.setAttribute('aria-activedescendant', `palette-${active}`);
  }

  function pick(command) {
    close();
    onPick(command);
  }

  function refresh() {
    items = filterCommands(commands(), input.value);
    active = 0;
    if (items.length) draw();
    else close();
  }

  input.addEventListener('input', refresh);
  input.addEventListener('blur', close);
  input.addEventListener('keydown', (event) => {
    if (list.hidden) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      active = (active + (event.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
      draw();
      event.preventDefault();
    } else if (event.key === 'Tab' || (event.key === 'Enter' && !event.shiftKey)) {
      pick(items[active]);
      event.preventDefault();
      event.stopImmediatePropagation();
    } else if (event.key === 'Escape') {
      close();
      event.preventDefault();
    }
  }, true);

  return { close, refresh };
}

/** asks before a dangerous command: resolves true when confirmed */
export function askConfirm({ dialog, message, ok, cancel, text }) {
  message.textContent = text;
  return new Promise((resolve) => {
    const done = (value) => {
      dialog.close();
      ok.removeEventListener('click', yes);
      cancel.removeEventListener('click', no);
      dialog.removeEventListener('cancel', no);
      resolve(value);
    };
    const yes = () => done(true);
    const no = () => done(false);
    ok.addEventListener('click', yes);
    cancel.addEventListener('click', no);
    dialog.addEventListener('cancel', no);
    dialog.showModal();
  });
}
