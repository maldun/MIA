// Markdown of the messages: marked parses, DOMPurify cleans. Only the output of renderMarkdown goes into the page.
// Libraries are vendored (../vendor, see VENDOR.md); nothing is loaded from the internet.
import { marked } from '../vendor/marked.esm.js';
import DOMPurify from '../vendor/purify.es.js';

const ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'b', 'i', 'del', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img'];
const ALLOWED_ATTR = ['href', 'src', 'alt', 'title', 'target', 'rel'];

export function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

export function parseMarkdown(text) {
  return marked.parse(String(text ?? ''), { gfm: true, breaks: true, async: false });
}

let hooked = false;
function installHooks(origin) {
  if (hooked) return;
  hooked = true;
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A') {
      node.setAttribute('target', '_blank');
      node.setAttribute('rel', 'noopener noreferrer');
    }
    if (node.tagName === 'IMG') {
      // images only from this server (the page loads nothing from other hosts)
      const src = node.getAttribute('src') || '';
      let same = false;
      if (!src) {
        node.remove();
        return;
      }
      try {
        same = new URL(src, origin).origin === origin;
      } catch (error) {
        same = false;
      }
      if (!same) node.remove();
    }
  });
}

/** safe HTML for a message; falls back to escaped text where DOMPurify cannot run (no DOM) */
export function renderMarkdown(text, origin = globalThis.location?.origin ?? 'http://localhost') {
  const html = parseMarkdown(text);
  if (!DOMPurify.isSupported) return `<p>${escapeHtml(text)}</p>`;
  installHooks(origin);
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    ALLOWED_URI_REGEXP: /^(?:https?:|mailto:|\/|#)/i,
  });
}
