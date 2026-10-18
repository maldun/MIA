// Settings and keyboard shortcuts: node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULTS, normalizeSettings, enterSends, initSettings } from '../../templates/static/chat/settings.js';
import { shortcutFor, isTypingTarget } from '../../templates/static/chat/a11y.js';
import { createStorage } from '../../templates/static/chat/storage.js';

function memoryStorage() {
  const data = new Map();
  return createStorage({ getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, v), removeItem: (k) => data.delete(k) });
}

test('settings: defaults, and damaged data falls back per field', () => {
  assert.deepEqual(normalizeSettings(undefined), DEFAULTS);
  assert.deepEqual(normalizeSettings('text'), DEFAULTS);
  const mixed = normalizeSettings({ enterSends: 'sometimes', showMood: false, compact: 'yes', showTimes: true });
  assert.equal(mixed.enterSends, 'auto');
  assert.equal(mixed.showMood, false);
  assert.equal(mixed.compact, false);
  assert.equal(mixed.showTimes, true);
});

test('Enter key modes', () => {
  assert.equal(enterSends('auto', false), true);
  assert.equal(enterSends('auto', true), false);
  assert.equal(enterSends('enter', true), true);
  assert.equal(enterSends('newline', false), false);
});

test('settings are stored, applied to the page and reset', () => {
  const storage = memoryStorage();
  const root = { dataset: {} };
  const seen = [];
  const settings = initSettings({ storage, root, onChange: (v) => seen.push(v) });
  assert.equal(root.dataset.compact, 'false');
  settings.set('compact', true);
  settings.set('showTimes', false);
  assert.equal(root.dataset.compact, 'true');
  assert.equal(root.dataset.times, 'false');
  assert.equal(seen.at(-1).compact, true);

  // the next page view reads them again
  const again = initSettings({ storage, root: { dataset: {} } });
  assert.equal(again.get().compact, true);
  assert.equal(again.get().showTimes, false);

  settings.reset();
  assert.deepEqual(settings.get(), DEFAULTS);
  assert.equal(root.dataset.compact, 'false');
  assert.equal(initSettings({ storage, root: { dataset: {} } }).get().compact, false);
});

test('broken stored settings never break the page', () => {
  const storage = memoryStorage();
  storage.set('mia.settings', '{not json');
  assert.deepEqual(initSettings({ storage, root: { dataset: {} } }).get(), DEFAULTS);
});

test('shortcuts', () => {
  const key = (k, extra = {}) => ({ key: k, ctrlKey: false, metaKey: false, altKey: false, ...extra });
  assert.equal(shortcutFor(key('/')), 'composer');
  assert.equal(shortcutFor(key('/'), true), null);          // typing a slash in the composer is just a slash
  assert.equal(shortcutFor(key('ArrowDown', { altKey: true })), 'latest');
  assert.equal(shortcutFor(key('c', { altKey: true })), 'toggle');
  assert.equal(shortcutFor(key('M', { altKey: true })), 'menu');
  assert.equal(shortcutFor(key('c', { ctrlKey: true })), null);   // copy stays copy
  assert.equal(shortcutFor(key('x', { altKey: true })), null);
  assert.equal(shortcutFor(key('a')), null);
});

test('typing targets', () => {
  assert.equal(isTypingTarget({ tagName: 'TEXTAREA' }), true);
  assert.equal(isTypingTarget({ tagName: 'SELECT' }), true);
  assert.equal(isTypingTarget({ tagName: 'BUTTON' }), false);
  assert.equal(isTypingTarget(null), false);
});
