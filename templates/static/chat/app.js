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
import { initChat } from './chat.js';
import { initLogin } from './login.js';
import { createApi } from './api.js';
import { initWorkspace } from './workspace.js';
import { initAccount } from './account.js';
import { variantLabel } from './panels-model.js';
import { initMood } from './mood.js';
import { askConfirm, initPalette, loadCommands } from './palette.js';
import { modelLabel } from './chat-model.js';
import { initCaption } from './caption.js';
import { initViewMenu } from './view-menu.js';
import { enterSends, initSettings } from './settings.js';
import { initAnnouncements, initShortcuts } from './a11y.js';

const $ = (id) => document.getElementById(id);
const EDITOR_TOKEN_KEY = 'mia_token';      // the same key the character (preset_api.gd) uses
const storage = defaultStorage();
const params = new URLSearchParams(location.search);

const lang = pickLanguage(location.search, storage.get('mia.lang'));
await loadLanguage(lang);
document.documentElement.lang = lang;
applyTranslations(document);
document.title = t('app.title');

const theme = initTheme({ storage, search: location.search });
let mood = null;
let started = false;      // the setting callback runs once while the page is built
const settings = initSettings({
  storage,
  onChange(values) {
    mood?.setEnabled(values.showMood);
    if (started) sendInset();
  },
});

const layout = initLayout({
  storage,
  panel: $('panel'),
  resizeHandle: $('panel-resize'),
  sheetHandle: $('sheet-handle'),
  collapseButton: $('collapse-button'),
  openButton: $('panel-open'),
  moodChip: $('mood'),
});

// --- connection: header, banner, history after (re)connecting --------------------------------------------
let composer = null;
let chat = null;
let sound = null;

function showState(state) {
  $('connection').dataset.state = state;
  $('connection-text').textContent = t(`connection.${state}`);
  const banner = $('banner');
  banner.hidden = state === 'online' || state === 'connecting';
  banner.dataset.state = state;
  banner.textContent = t(state === 'reconnecting' ? 'banner.reconnecting' : 'banner.offline');
  composer?.setOnline(state === 'online' || state === 'connecting');
  if (state === 'online') {
    sound?.connected();      // this page may play the voice (only one page does)
    chat?.loadLatest();      // first load, and what was missed while offline
  }
}
// a server with accounts (IF-101) answers 401 without a session: the login asks and the page reloads with the session cookie
const login = initLogin({
  dialog: $('login'),
  form: $('login-form'),
  userInput: $('login-user'),
  passwordInput: $('login-password'),
  errorLine: $('login-error'),
  submitButton: $('login-submit'),
  storage,
  t,
  onSuccess: () => location.reload(),
});
const socket = connect(showState, location.origin, () => login.open());
const api = createApi({ onLoginRequired: () => login.open() });

// --- the character: framing in the free area, camera view, background, captions -----------------------------
let viewMenu = null;
let insetFrame = 0;

/** tells the character how much of the window the chat covers (at most once per frame, also while the sheet moves) */
function sendInset() {
  if (insetFrame) return;
  insetFrame = window.requestAnimationFrame(() => {
    insetFrame = 0;
    character.setInset(layout.inset());
  });
}

const character = initCharacter({
  frame: $('character'),
  socket,
  enabled: params.get('character') !== '0',
  onReady() {
    sendInset();
    viewMenu?.apply();
  },
  onFailed() {
    $('character-notice').hidden = false;
  },
});

const caption = initCaption({ el: $('caption'), socket, isCollapsed: () => layout.collapsed });
layout.onChange(() => {
  sendInset();
  caption.update();
});
new ResizeObserver(sendInset).observe($('panel'));
new ResizeObserver(sendInset).observe($('mood'));
window.addEventListener('resize', sendInset);

sound = initSound({
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

const menu = initMenu({
  button: $('menu-button'),
  menu: $('menu'),
  themeButtons: document.querySelectorAll('[data-theme-choice]'),
  theme,
  aboutButton: $('about-button'),
  aboutDialog: $('about'),
  aboutClose: $('about-close'),
});

// --- the views of IF-101 v1: workspace (records, trust, persona, score), account, the variant label ---------------------
const workspace = initWorkspace({ dialog: $('workspace'), tabsEl: $('workspace-tabs'), body: $('workspace-body'), closeButton: $('workspace-close'), api, socket, t, notify: toast });
const account = initAccount({
  dialog: $('account'), nameEl: $('account-name'), form: $('account-form'), oldInput: $('account-old'), newInput: $('account-new'), repeatInput: $('account-repeat'),
  errorLine: $('account-error'), closeButton: $('account-close'), api, storage, t, notify: toast,
});
$('workspace-button').addEventListener('click', () => { menu.close(false); workspace.open(); });
$('account-button').addEventListener('click', () => { menu.close(false); account.open(); });
socket.on('variant', (data) => {
  const label = variantLabel(data?.name, t);
  $('variant').textContent = label;
  $('variant').hidden = !label;
  character.setVariant(data?.name);                    // the outfit of the workflow that answers; null = the chat's variant
});

viewMenu = initViewMenu({
  buttons: document.querySelectorAll('[data-view]'),
  group: $('background-group'),
  select: $('background-select'),
  character,
  storage,
  t,
});

// --- mood line and header chip, driven by the server --------------------------------------------------
mood = initMood({ chip: $('mood'), emoji: $('mood-emoji'), text: $('mood-text'), live: $('mood-live'), enabled: settings.get().showMood });

socket.on('chat_status', (status) => {
  mood.update(status.mood, status.activity);
  composer?.setBusy(status.busy && (status.activity === 'thinking' || status.activity === 'speaking'));
  const chip = $('model-chip');
  const label = modelLabel(status.profile);
  chip.hidden = !label;
  chip.textContent = label ? t(`chip.${label}`) : '';
  chip.title = status.model ?? '';
});

// --- the conversation --------------------------------------------------------------------------------
function toast(message) {
  chat.note(message);
  const live = $('mood-live');
  live.textContent = message;
}

chat = initChat({
  list: $('messages'), empty: $('empty'), jump: $('jump'), olderButton: $('older'), socket, render: renderMarkdown, t, notify: toast,
  me: () => storage.get('mia.account') || null,
  onLoginRequired: () => login.open(),
  api,
});

let commands = [];
loadCommands().then((list) => { commands = list; });

const suggestions = document.querySelectorAll('[data-suggestion]');
for (const suggestion of suggestions) suggestion.dataset.text = t(suggestion.dataset.suggestion);

initPalette({
  input: $('input'),
  list: $('palette'),
  commands: () => commands,
  onPick: (command) => composer.fill(command.command),
});

composer = initComposer({
  form: $('composer'),
  input: $('input'),
  send: $('send'),
  stop: $('stop'),
  counter: $('counter'),
  storage,
  suggestions,
  async onSend(text) {
    const command = commands.find((c) => c.command === text.toLowerCase());
    if (command?.confirm) {
      const ok = await askConfirm({
        dialog: $('confirm'),
        message: $('confirm-text'),
        ok: $('confirm-ok'),
        cancel: $('confirm-cancel'),
        text: t('confirm.command', { command: command.command, description: command.description }),
      });
      if (!ok) return false;
    }
    chat.send(text);
    return true;
  },
  onStop: () => socket.emit('chat_stop'),
  enterSends: () => enterSends(settings.get().enterSends, window.matchMedia?.('(pointer: coarse)').matches ?? false),
});

// --- settings of this device, keyboard shortcuts, announcements for screen readers ------------------------------
initAnnouncements({ region: $('announce'), socket, list: $('messages'), t });
initShortcuts({ composer, layout, menu, chat });

const fields = { enterSends: $('set-enter'), showMood: $('set-mood'), showEmotions: $('set-emotions'), showTimes: $('set-times'), compact: $('set-compact') };

function showSettings(values) {
  fields.enterSends.value = values.enterSends;
  tokenField.value = storage.get(EDITOR_TOKEN_KEY, '') ?? '';
  for (const key of ['showMood', 'showEmotions', 'showTimes', 'compact']) fields[key].checked = values[key];
}

for (const [key, field] of Object.entries(fields)) {
  field.addEventListener('change', () => settings.set(key, field.type === 'checkbox' ? field.checked : field.value));
}
// the editor token: a normal input of the page (reliable focus and paste); the character reads the same stored value
const tokenField = $('set-token');
tokenField.addEventListener('input', () => {
  const value = tokenField.value.trim();
  if (value) storage.set(EDITOR_TOKEN_KEY, value);
  else storage.remove(EDITOR_TOKEN_KEY);
});

$('settings-reset').addEventListener('click', () => {
  settings.reset();
  theme.set('auto');
  showSettings(settings.get());
});
$('settings-button').addEventListener('click', () => {
  menu.close(false);
  showSettings(settings.get());
  $('settings').showModal();
});

started = true;

// handle for tests and debugging
window.miaChat = { renderMarkdown, socket, theme, chat, mood, composer, settings, sound, character };
