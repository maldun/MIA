// PROTOTYPE helper: runs the page's own app.js in node with a stand-in DOM against a running viewer backend, and drives it like a person.
// usage: node proto_checks/e2e_page.mjs <base url> <scenario>   (the page files are copied next to graph_app first, as the server serves them)
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';
const [base, scenario] = [process.argv[2], process.argv[3] ?? 'playback'];
const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'e2e-'));
for (const dir of ['graph_app', 'graph_app_v2']) for (const f of fs.readdirSync(path.join(repo, dir))) if (fs.statSync(path.join(repo, dir, f)).isFile()) fs.copyFileSync(path.join(repo, dir, f), path.join(tmp, f));
const html = fs.readFileSync(path.join(repo, 'graph_app_v2/index.html'), 'utf8');
const els = {};
const make = (id) => ({ id, hidden: false, disabled: false, _t: '', value: '', checked: false, children: [], listeners: {}, attrs: {}, classList: { add() {}, remove() {}, toggle() {} }, style: {}, tabIndex: 0,
  get textContent() { return this._t; }, set textContent(v) { this._t = String(v); },
  setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k]; }, addEventListener(t, f) { (this.listeners[t] ??= []).push(f); }, replaceChildren(...c) { this.children = c; }, append(...c) { this.children.push(...c); },
  focus() {}, contains() { return false; }, click() { return Promise.all((this.listeners.click ?? []).map((f) => f({ target: this, preventDefault() {} }))); } });
for (const m of html.matchAll(/id="([^"]+)"/g)) els[m[1]] = make(m[1]);
globalThis.document = { getElementById: (id) => els[id] ?? (els[id] = make(id)), createElement: (tag) => ({ ...make(''), tag }), addEventListener() {}, documentElement: {} };
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '#888' });
globalThis.window = { localStorage: null };
class DataSet { constructor(d) { this.d = d; } }
const nets = [];
globalThis.vis = { DataSet, Network: class { constructor(c, data) { this.data = data; nets.push(this); } on() {} destroy() {} setOptions() {} selectNodes() {} getPositions() { return {}; } } };
let cookie = '';
const real = globalThis.fetch;
globalThis.fetch = async (url, opts = {}) => { const r = await real(base + url, { ...opts, headers: { ...(opts.headers ?? {}), Origin: base, Cookie: cookie } }); const c = r.headers.get('set-cookie'); if (c) cookie = c.split(';')[0]; return r; };
await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user: 'owner', password: 'secret' }) });
const wait = async (ms = 150) => new Promise((r) => setTimeout(r, ms));
await import(path.join(tmp, 'app.js'));
await wait(600);
const log = (...a) => console.log(...a);
const pickGraph = async (id) => { const li = els.list.children.find((c) => c.textContent.startsWith(id)); await li.listeners.click[0](); await wait(400); };
const pickVersion = async (v) => { const li = els.history.children.find((c) => c.textContent.includes(`v${v}`) || c.textContent.startsWith(`${v}`) || c.textContent.includes(`ersion ${v}`)); if (!li) throw new Error('no history entry for version ' + v + ': ' + els.history.children.map((c) => c.textContent).join(' | ')); await li.listeners.click[0](); await wait(400); };
if (scenario === 'playback') {
  const target = process.argv[4] ?? 'cp2.multi'; const version = Number(process.argv[5] ?? 5);
  await pickGraph(target); await pickVersion(version);
  log('how:', els.how.children.map((c) => c.textContent).join(' || '));
  await els.play.click(); await wait(400);
  const show = (tag) => log(tag, '| fwd disabled:', els['rp-fwd'].disabled, '| back disabled:', els['rp-back'].disabled, '|', els['rp-fwd'].textContent, '|', els['rp-back'].textContent, '| bar hidden:', els['replay-bar'].hidden, '| status:', els.status.textContent.slice(0, 140), '| nodes:', nets.at(-1)?.data.nodes.d.length);
  show('start');
  for (let i = 1; i <= 4; i++) { await els['rp-fwd'].click(); await wait(300); show('after forward ' + i); }
  await els['rp-back'].click(); await wait(300); show('after back');
}
process.exit(0);
