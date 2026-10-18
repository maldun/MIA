// Entry point of the chat page: wires the modules together. No inline scripts (strict CSP).
import { defaultStorage } from './storage.js';
import { applyTranslations, loadLanguage, pickLanguage, t } from './i18n.js';
import { initTheme } from './theme.js';
import { initLayout } from './layout.js';
import { renderMarkdown } from './markdown.js';
import { connect } from './socket.js';
import { initCharacter } from './character.js';
import { initSound } from './sound.js';
import { initMenu } from './menu.js';
import { initComposer } from './composer.js';
import { initChatLite } from './chat-lite.js';

const $ = (id) => document.getElementById(id);
const storage = defaultStorage();
const params = new URLSearchParams(location.search);

const lang = pickLanguage(location.search, storage.get('mia.lang'));
await loadLanguage(lang);
document.documentElement.lang = lang;
applyTranslations(document);
document.title = t('app.title');

const theme = initTheme({ storage, search: location.search });

initLayout({
  storage,
  panel: $('panel'),
  resizeHandle: $('panel-resize'),
  sheetHandle: $('sheet-handle'),
  collapseButton: $('collapse-button'),
  openButton: $('panel-open'),
});

// connection state in the header
const connection = $('connection');
function showState(state) {
  connection.dataset.state = state;
  $('connection-text').textContent = t(`connection.${state}`);
}
const socket = connect(showState);

const character = initCharacter({ frame: $('character'), socket, enabled: params.get('character') !== '0' });

initSound({
  audio: $('audio'),
  socket,
  character,
  storage,
  muteToggle: $('mute-toggle'),
  muteLabel: $('mute-label'),
  muteIcon: $('mute-icon'),
  volume: $('volume'),
  hint: $('sound-hint'),
  t,
});

initMenu({
  button: $('menu-button'),
  menu: $('menu'),
  themeButtons: document.querySelectorAll('[data-theme-choice]'),
  theme,
  aboutButton: $('about-button'),
  aboutDialog: $('about'),
  aboutClose: $('about-close'),
});

const chat = initChatLite({ list: $('messages'), empty: $('empty'), jump: $('jump'), render: renderMarkdown, t });

const suggestions = document.querySelectorAll('[data-suggestion]');
for (const suggestion of suggestions) suggestion.dataset.text = t(suggestion.dataset.suggestion);

initComposer({
  form: $('composer'),
  input: $('input'),
  send: $('send'),
  storage,
  suggestions,
  onSend(text) {
    if (!socket.connected) {
      chat.note(t('chat.sending_failed'));
      return false;
    }
    socket.emit('message', text);
    chat.user(text);
    return true;
  },
});

socket.on('answer', (text) => chat.answer(String(text ?? '')));

// handle for tests and debugging
window.miaChat = { renderMarkdown, socket, theme, chat };
