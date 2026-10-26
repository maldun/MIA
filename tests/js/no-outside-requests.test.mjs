// No request of the chat page leaves the host (N-1.3 T-04, TC-VPB-004, REQ-FE-026): the sources name no address outside the page's own host.
// A browser test that records every request of a session is the second line (stage 2); this one runs in the commit gate. node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const STATIC = new URL('../../templates/static/chat/', import.meta.url).pathname;
const INDEX = new URL('../../templates/index.html', import.meta.url).pathname;
const ALLOWED = [/^http:\/\/www\.w3\.org\/(2000\/svg|1999\/xlink|1998\/Math\/MathML)/];         // XML namespaces are names, not addresses

function sources() {
  const files = readdirSync(STATIC).filter((f) => f.endsWith('.js') || f.endsWith('.css')).map((f) => join(STATIC, f));
  return [INDEX, ...files].map((path) => ({ path, text: readFileSync(path, 'utf8') }));
}

test('TC-VPB-004: no source of the chat page names an address outside the host', () => {
  const found = [];
  for (const { path, text } of sources()) {
    for (const match of text.matchAll(/(?:https?:)?\/\/[A-Za-z0-9.-]+\.[a-z]{2,}[^\s"'`)]*/g)) {
      const url = match[0];
      if (!ALLOWED.some((rule) => rule.test(url))) found.push(`${path.split('/').pop()}: ${url}`);
    }
  }
  assert.deepEqual(found, []);
});

test('TC-VPB-004: the page loads its scripts and styles from its own host only', () => {
  const html = readFileSync(INDEX, 'utf8');
  for (const match of html.matchAll(/(?:src|href)="([^"]+)"/g)) {
    const value = match[1];
    assert.ok(!/^(?:https?:)?\/\//.test(value), `external reference in index.html: ${value}`);
  }
});

test('TC-VPB-004: the voice player only reads the url the server gave it (relative to the host)', () => {
  const text = readFileSync(join(STATIC, 'sound.js'), 'utf8');
  assert.ok(!/fetch\(|XMLHttpRequest|new WebSocket/.test(text), 'sound.js makes no request of its own');
  assert.ok(text.includes("data?.url ?? '/audio/out.wav'"));
});
