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

// --- the run report (A-154, REQ-CLV-049, 052): the one text of a run that may hold links; its own rules, the chat messages above keep theirs ---
const REPORT_TAGS = ['p', 'br', 'strong', 'em', 'b', 'i', 'del', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'];      // no img, form, frame, style or script
const REPORT_ADDRESS = /^https?:\/\/[^\s\u0000-\u001f\u007f]+$/i;

/** the address of a link in a run report, or null: only http and https addresses without spaces or control characters are links (REQ-CLV-049) */
export function reportHref(href) {
  return typeof href === 'string' && REPORT_ADDRESS.test(href) ? href : null;
}

/** safe HTML for a run report: only reportHref addresses are links (new tab, noopener noreferrer), no image, form, frame, style, script or event handler (REQ-CLV-049, 052);
 *  escaped text where DOMPurify cannot run. No DOMPurify hook is used: hooks are global to the library and would change how the messages of the chat are cleaned. */
export function renderReport(text) {
  const html = parseMarkdown(text);
  if (!DOMPurify.isSupported) return `<p>${escapeHtml(text)}</p>`;
  const clean = DOMPurify.sanitize(html, { ALLOWED_TAGS: REPORT_TAGS, ALLOWED_ATTR: ['href', 'title'], ALLOW_DATA_ATTR: false, ALLOWED_URI_REGEXP: /^https?:\/\//i });
  const page = document.createElement('template');
  page.innerHTML = clean;
  for (const link of page.content.querySelectorAll('a')) {
    if (reportHref(link.getAttribute('href'))) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    } else {
      link.replaceWith(...link.childNodes);      // an address that is not a web address stays text
    }
  }
  return page.innerHTML;
}
