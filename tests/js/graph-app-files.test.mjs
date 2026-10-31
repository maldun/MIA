// The files of the Graph app (N-5 T-01, reworked for vis-network by D-124): REQ-GA-009 (plain stack, the graph library vendored, no build step)
// and REQ-GA-010 (no outside request). The browser test of TC-GA-010 is the second line (stage 2, T-06); this one runs in the commit gate.
// node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const APP = new URL('../../graph_app/', import.meta.url).pathname;
const VENDOR = join(APP, 'vendor', 'vis-network.min.js');
const ALLOWED = [/^http:\/\/www\.w3\.org\/(2000\/svg|1999\/xlink|1998\/Math\/MathML)/];         // XML namespaces are names, not addresses
const OUTSIDE = /(?:https?:)?\/\/[A-Za-z0-9.-]+\.[a-z]{2,}[^\s"'`)]*/g;

function ownSources() {
  return readdirSync(APP).filter((f) => /\.(html|js|css)$/.test(f)).map((f) => ({ name: f, text: readFileSync(join(APP, f), 'utf8') }));
}

test('REQ-GA-010: no own source of the Graph app names an address outside the host', () => {
  // Given
  const sources = ownSources();
  // When
  const found = [];
  for (const { name, text } of sources) {
    for (const match of text.matchAll(OUTSIDE)) {
      if (!ALLOWED.some((rule) => rule.test(match[0]))) found.push(`${name}: ${match[0]}`);
    }
  }
  // Then
  assert.deepEqual(sources.map((s) => s.name).sort(), ['app.js', 'graph-view.js', 'graph.css', 'index.html']);
  assert.deepEqual(found, []);
});

test('REQ-GA-010: the page loads its style and scripts from its own folder, the graph library from vendor/', () => {
  // Given
  const html = readFileSync(join(APP, 'index.html'), 'utf8');
  // When
  const refs = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map((m) => m[1]);
  // Then
  assert.deepEqual(refs, ['graph.css', 'vendor/vis-network.min.js', 'app.js']);
});

test('REQ-GA-010: the vendored graph library makes no request of its own', () => {
  // Given
  const text = readFileSync(VENDOR, 'utf8');
  // When
  const urls = [...text.matchAll(/url\(([^)]*)\)/g)].map((m) => m[1]);
  // Then
  assert.ok(!text.includes('XMLHttpRequest'));
  assert.ok(!text.includes('fetch('));
  assert.ok(urls.length > 0);
  assert.ok(urls.every((u) => u.startsWith('"data:')), urls.filter((u) => !u.startsWith('"data:')).join(' '));
});

test('REQ-GA-009: the graph library is in the repository with its version and checksum named in vendor/README.md', () => {
  // Given
  const readme = readFileSync(join(APP, 'vendor', 'README.md'), 'utf8');
  // When
  const sha = createHash('sha256').update(readFileSync(VENDOR)).digest('hex');
  // Then
  assert.ok(readme.includes(sha), sha);
  assert.ok(readme.includes('10.1.2'));
  assert.ok(readFileSync(VENDOR, 'utf8').includes('@version 10.1.2'));
});

test('REQ-GA-009: the Graph app has no bundler files and no build step', () => {
  // Given
  const names = ['package.json', 'package-lock.json', 'node_modules', 'webpack.config.js', 'vite.config.js', 'rollup.config.js', 'tsconfig.json'];
  // When
  const present = names.filter((name) => existsSync(join(APP, name)));
  // Then
  assert.deepEqual(present, []);
});
