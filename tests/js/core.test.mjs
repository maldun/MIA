// Pure parts of the chat page: node --test tests/js/
import test from 'node:test';
import assert from 'node:assert/strict';
import { createStorage } from '../../templates/static/chat/storage.js';
import { pickLanguage, setDictionaries, t } from '../../templates/static/chat/i18n.js';
import { normalizeTheme, themeFromSearch, resolveTheme } from '../../templates/static/chat/theme.js';
import { layoutMode, clampPanelWidth, nearestSnap, nextSnap, snapHeights, occupiedWidth } from '../../templates/static/chat/layout.js';
import { normalizeMessage } from '../../templates/static/chat/composer.js';
import { renderMarkdown, parseMarkdown } from '../../templates/static/chat/markdown.js';

test('storage works when the backend throws', () => {
  const broken = { getItem() { throw new Error('x'); }, setItem() { throw new Error('x'); }, removeItem() { throw new Error('x'); } };
  const storage = createStorage(broken);
  assert.equal(storage.get('a', 'fb'), 'fb');
  assert.equal(storage.set('a', 1), false);
  assert.equal(storage.get('a'), '1');
  storage.remove('a');
  assert.equal(storage.get('a', 'fb'), 'fb');
});

test('storage uses the backend', () => {
  const data = new Map();
  const storage = createStorage({ getItem: (k) => data.get(k) ?? null, setItem: (k, v) => data.set(k, v), removeItem: (k) => data.delete(k) });
  storage.set('k', 'v');
  assert.equal(data.get('k'), 'v');
  assert.equal(storage.get('k'), 'v');
});

test('i18n: language choice, fallback, placeholders', () => {
  assert.equal(pickLanguage('?lang=de'), 'de');
  assert.equal(pickLanguage('?lang=xx', 'de'), 'de');
  assert.equal(pickLanguage('', 'fr'), 'en');
  setDictionaries({ a: 'A {n}', b: 'B' }, { a: 'Ä {n}' });
  assert.equal(t('a', { n: 3 }), 'Ä 3');
  assert.equal(t('b'), 'B');
  assert.equal(t('missing'), 'missing');
  assert.equal(t('a'), 'Ä {n}');
});

test('theme rules', () => {
  assert.equal(normalizeTheme('nope'), 'auto');
  assert.equal(themeFromSearch('?theme=light'), 'light');
  assert.equal(themeFromSearch('?theme=x'), null);
  assert.equal(resolveTheme('auto', true), 'light');
  assert.equal(resolveTheme('dark', true), 'dark');
});

test('layout rules', () => {
  assert.equal(layoutMode(1440, 900), 'panel');
  assert.equal(layoutMode(360, 740), 'sheet');
  assert.equal(layoutMode(768, 1024), 'sheet');
  assert.equal(layoutMode(740, 360), 'panel');
  assert.equal(clampPanelWidth(100, 1440), 320);
  assert.equal(clampPanelWidth(900, 1440), 640);
  assert.equal(clampPanelWidth(900, 700), 556);
  assert.equal(nextSnap('peek', 1), 'half');
  assert.equal(nextSnap('full', 1), 'full');
  assert.equal(nextSnap('peek', -1), 'peek');
  assert.equal(nextSnap('bogus', 1), 'full');
  const heights = snapHeights(800);
  assert.equal(nearestSnap(heights.full - 5, 800), 'full');
  assert.equal(nearestSnap(heights.peek + 5, 800), 'peek');
  assert.equal(occupiedWidth({ mode: 'panel', collapsed: false, panelWidth: 400 }), 424);
  assert.equal(occupiedWidth({ mode: 'panel', collapsed: true, panelWidth: 400 }), 0);
  assert.equal(occupiedWidth({ mode: 'sheet', collapsed: false, panelWidth: 400 }), 0);
});

test('messages are normalized', () => {
  assert.equal(normalizeMessage('  hi\u0000 there \n'), 'hi there');
  assert.equal(normalizeMessage('a\nb'), 'a\nb');
  assert.equal(normalizeMessage('x'.repeat(9000)).length, 8000);
  assert.equal(normalizeMessage(null), '');
});

test('markdown parses; without a DOM the output is escaped text', () => {
  assert.match(parseMarkdown('**bold**'), /<strong>bold<\/strong>/);
  const html = renderMarkdown('<img src=x onerror=alert(1)>');
  assert.doesNotMatch(html, /<img/);
});
