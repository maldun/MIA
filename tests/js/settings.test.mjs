// Settings and shortcuts of the chat page: node --test tests/js/
import test from 'node:test';
import assert from 'node:assert/strict';
import { createStorage } from '../../templates/static/chat/storage.js';
import { DEFAULTS, clampHue, initSettings, loadSettings } from '../../templates/static/chat/settings.js';
import { actionFor, isTyping } from '../../templates/static/chat/shortcuts.js';

function memoryStorage() {
  const data = new Map();
  return createStorage({ getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, v), removeItem: (k) => data.delete(k) });
}
function fakeRoot() {
  const vars = {};
  return { dataset: {}, style: { setProperty: (k, v) => { vars[k] = v; } }, vars };
}

test('settings: defaults, change, persist, reset', () => {
  const storage = memoryStorage();
  const root = fakeRoot();
  const seen = [];
  const settings = initSettings({ storage, root, onChange: (s, key) => seen.push(key) });
  assert.deepEqual(settings.get(), DEFAULTS);
  assert.equal(root.dataset.compact, '0');
  settings.set('compact', true);
  settings.set('accent', 330);
  settings.set('nonsense', true);
  assert.equal(root.dataset.compact, '1');
  assert.equal(root.vars['--accent-h'], '330');
  assert.deepEqual(seen, ['compact', 'accent']);
  assert.equal(loadSettings(storage).compact, true);
  assert.equal(loadSettings(storage).accent, 330);
  storage.set('mia.view', 'face');
  settings.reset(['mia.view']);
  assert.deepEqual(settings.get(), DEFAULTS);
  assert.equal(storage.get('mia.view'), null);
  assert.equal(root.dataset.compact, '0');
});

test('settings work with a failing storage', () => {
  const broken = { getItem() { throw new Error('x'); }, setItem() { throw new Error('x'); }, removeItem() { throw new Error('x'); } };
  const settings = initSettings({ storage: createStorage(broken), root: fakeRoot() });
  settings.set('mood', false);
  assert.equal(settings.get().mood, false);
});

test('settings: hue is clamped, garbage values fall back', () => {
  assert.equal(clampHue(999), 360);
  assert.equal(clampHue(-5), 0);
  assert.equal(clampHue('abc'), DEFAULTS.accent);
  const storage = memoryStorage();
  storage.set('mia.setting.accent', 'zzz');
  storage.set('mia.setting.sendOnEnter', '0');
  assert.equal(loadSettings(storage).accent, DEFAULTS.accent);
  assert.equal(loadSettings(storage).sendOnEnter, false);
});

test('shortcuts: keys map to actions, typing blocks the plain ones', () => {
  const body = { tagName: 'BODY' };
  const field = { tagName: 'TEXTAREA' };
  assert.equal(actionFor({ key: '/', target: body }), 'focus');
  assert.equal(actionFor({ key: '/', target: field }), null);
  assert.equal(actionFor({ key: '?', target: body }), 'help');
  assert.equal(actionFor({ key: 'h', altKey: true, target: field }), 'collapse');
  assert.equal(actionFor({ key: 'End', altKey: true, target: body }), 'latest');
  assert.equal(actionFor({ key: ',', altKey: true, target: body }), 'settings');
  assert.equal(actionFor({ key: 'h', ctrlKey: true, target: body }), null);
  assert.equal(isTyping({ tagName: 'DIV', isContentEditable: true }), true);
});
