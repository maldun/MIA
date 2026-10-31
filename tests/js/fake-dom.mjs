// A small fake DOM for the page-wiring tests of N-1.1 (F6 of the verification): enough of Element, document and events for chat.js,
// workspace.js, task-card.js and account.js. No dependency (jsdom is not installed); selectors: tag, .class, #id, [attr], [attr=value],
// compounds of these, descendant chains and comma lists. innerHTML keeps the markup as text (the tests read textContent).

const camel = (name) => name.replace(/-([a-z])/g, (_, c) => c.toUpperCase());

class FakeText {
  constructor(text) { this.nodeType = 3; this.textContent = String(text); this.parentElement = null; }
  remove() { this.parentElement?._drop(this); }
}

class FakeClassList {
  constructor(owner) { this.owner = owner; }
  get items() { return this.owner.className.split(/\s+/).filter(Boolean); }
  contains(name) { return this.items.includes(name); }
  add(...names) { this.owner.className = [...new Set([...this.items, ...names])].join(' '); }
  remove(...names) { this.owner.className = this.items.filter((n) => !names.includes(n)).join(' '); }
  toggle(name, force) {
    const on = force === undefined ? !this.contains(name) : Boolean(force);
    if (on) this.add(name); else this.remove(name);
    return on;
  }
}

export class FakeElement {
  constructor(tag, doc) {
    this.nodeType = 1;
    this.tagName = tag.toUpperCase();
    this.ownerDocument = doc;
    this.className = '';
    this.classList = new FakeClassList(this);
    this.dataset = {};
    this.attributes = {};
    this.childNodes = [];
    this.parentElement = null;
    this.listeners = {};
    this.hidden = false;
    this.value = '';
    this.scrollTop = 0;
    this.scrollHeight = 0;
    this.clientHeight = 0;
    this.open = false;
  }

  get children() { return this.childNodes.filter((n) => n.nodeType === 1); }
  get textContent() { return this._html !== undefined ? this._html.replace(/<[^>]*>/g, '') : this.childNodes.map((n) => n.textContent).join(''); }
  set textContent(text) { this._clear(); if (text !== '' && text !== undefined && text !== null) this.append(String(text)); }
  set innerHTML(html) { this._clear(); this._html = String(html); }
  get innerHTML() { return this._html ?? this.textContent; }
  get previousElementSibling() { const s = this.parentElement?.children ?? []; return s[s.indexOf(this) - 1] ?? null; }
  get nextElementSibling() { const s = this.parentElement?.children ?? []; const i = s.indexOf(this); return i < 0 ? null : s[i + 1] ?? null; }
  get id() { return this.attributes.id ?? ''; }
  set id(value) { this.attributes.id = value; }

  _clear() { for (const n of this.childNodes) n.parentElement = null; this.childNodes = []; delete this._html; }
  _drop(node) { this.childNodes = this.childNodes.filter((n) => n !== node); node.parentElement = null; }
  _adopt(node) {
    const child = typeof node === 'string' ? new FakeText(node) : node;
    child.parentElement?._drop(child);
    child.parentElement = this;
    return child;
  }

  append(...nodes) { delete this._html; for (const node of nodes) this.childNodes.push(this._adopt(node)); }
  insertBefore(node, ref) {
    if (!ref) { this.append(node); return node; }
    const child = this._adopt(node);
    this.childNodes.splice(this.childNodes.indexOf(ref), 0, child);
    return child;
  }
  before(node) { this.parentElement.insertBefore(node, this); }
  remove() { this.parentElement?._drop(this); }
  replaceChildren(...nodes) { this._clear(); this.append(...nodes); }
  contains(node) { for (let n = node; n; n = n.parentElement) if (n === this) return true; return false; }

  setAttribute(name, value) { if (name.startsWith('data-')) this.dataset[camel(name.slice(5))] = String(value); else this.attributes[name] = String(value); }
  getAttribute(name) { return name.startsWith('data-') ? this.dataset[camel(name.slice(5))] ?? null : this.attributes[name] ?? null; }
  removeAttribute(name) { delete this.attributes[name]; if (name === 'src') this.src = undefined; }

  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  dispatchEvent(event) {
    event.target ??= this;
    event.defaultPrevented ??= false;
    event.preventDefault ??= () => { event.defaultPrevented = true; };
    for (let n = this; n; n = event.bubbles === false ? null : n.parentElement) for (const fn of n.listeners[event.type] ?? []) fn(event);
    return !event.defaultPrevented;
  }
  click() { return this.dispatchEvent({ type: 'click' }); }
  focus() { this.ownerDocument.activeElement = this; }
  scrollTo({ top }) { this.scrollTop = top; }

  // forms and dialogs
  requestSubmit() { this.dispatchEvent({ type: 'submit' }); }
  reset() { for (const input of this.querySelectorAll('input,textarea')) input.value = ''; }
  showModal() { this.open = true; }
  close() { this.open = false; }

  _all() { return this.children.flatMap((c) => [c, ...c._all()]); }
  querySelectorAll(selector) { return this._all().filter((n) => matches(n, selector, this)); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  matches(selector) { return matches(this, selector, null); }
  closest(selector) { for (let n = this; n; n = n.parentElement) if (n.nodeType === 1 && n.matches(selector)) return n; return null; }
}

function attribute(node, name) {
  if (name.startsWith('data-')) return node.dataset[camel(name.slice(5))];
  if (name === 'id') return node.id || undefined;
  return node.attributes[name] ?? (node[name] === undefined || node[name] === '' ? undefined : String(node[name]));
}

function compound(node, part) {
  const re = /([a-zA-Z][\w-]*)|\.([\w-]+)|#([\w-]+)|\[([\w-]+)(?:=["']?([^"'\]]*)["']?)?\]/g;
  for (const [, tag, cls, id, attr, value] of part.matchAll(re)) {
    if (tag && node.tagName !== tag.toUpperCase()) return false;
    if (cls && !node.classList.contains(cls)) return false;
    if (id && node.id !== id) return false;
    if (attr && (value === undefined ? attribute(node, attr) === undefined : attribute(node, attr) !== value)) return false;
  }
  return true;
}

function matches(node, selector, root) {
  return selector.split(',').some((one) => {
    const parts = one.trim().split(/\s+/);
    if (!compound(node, parts.at(-1))) return false;
    let at = node.parentElement;
    for (let i = parts.length - 2; i >= 0; i -= 1) {
      while (at && at !== root && !compound(at, parts[i])) at = at.parentElement;
      if (!at || at === root) return false;
      at = at.parentElement;
    }
    return true;
  });
}

/** a document with createElement and activeElement, installed as globalThis.document for the module under test */
export function installDocument() {
  const doc = { activeElement: null };
  doc.createElement = (tag) => new FakeElement(tag, doc);
  doc.createTextNode = (text) => new FakeText(text);
  doc.body = doc.createElement('body');
  globalThis.document = doc;
  return doc;
}

/** a socket that records what the page emits and lets the test send server events; `timeout(ms).emit(name, data, ack)` keeps the ack */
export function fakeSocket() {
  const handlers = {};
  const socket = {
    emitted: [],
    disconnected: 0,
    on(name, fn) { (handlers[name] ||= []).push(fn); },
    emit(name, data, ack) { socket.emitted.push({ name, data, ack }); },
    timeout() { return socket; },
    disconnect() { socket.disconnected += 1; },
    fire(name, payload) { for (const fn of handlers[name] ?? []) fn(payload); },
    handles(name) { return Boolean(handlers[name]?.length); },
  };
  return socket;
}

/** a window whose animation frames run when the test says so */
export function fakeWindow() {
  const frames = [];
  return {
    frames,
    requestAnimationFrame(fn) { frames.push(fn); return frames.length; },
    runFrames() { while (frames.length) frames.shift()(); },
    setTimeout() { return 0; },
    clearTimeout() {},
    setInterval() { return 0; },
  };
}

export const flush = () => new Promise((resolve) => setImmediate(resolve));
