// The 3D character lives in an iframe (same origin). Messages are JSON strings (postMessage), see ui/README.md.

export const LOAD_TIMEOUT_MS = 30000;

export function webglAvailable(doc = document) {
  try {
    const canvas = doc.createElement('canvas');
    return Boolean(canvas.getContext('webgl2'));
  } catch (error) {
    return false;
  }
}

/**
 * onReady: the character loaded (send it the current view and inset); onFailed(reason): no secure context, no WebGL, no answer in time or
 * the character itself said "failed" (IF-111); the chat then works full width and the page shows a small notice. onUnmapped(presets, gestures):
 * what a newly selected model cannot map. The character loads only on localhost or over HTTPS (a secure context, REQ-CHV-012).
 */
export function initCharacter({ frame, socket, origin = location.origin, enabled = true, onReady = () => {}, onFailed = () => {}, onUnmapped = () => {},
  win = window, secure = win.isSecureContext, hasWebgl = webglAvailable }) {
  let ready = false;
  let timer = 0;

  function send(message) {
    if (enabled && frame.contentWindow) frame.contentWindow.postMessage(JSON.stringify(message), origin);
  }

  function disable(failed, reason) {
    const wasEnabled = enabled;
    enabled = false;
    frame.removeAttribute('src');
    frame.hidden = true;
    win.clearTimeout(timer);
    if (failed && wasEnabled) onFailed(reason);          // reported once, whatever the cause
  }

  if (!enabled) {
    disable(false);
  } else if (!secure) {
    disable(true, 'insecure');
  } else if (!hasWebgl()) {
    disable(true, 'no WebGL');
  } else {
    timer = win.setTimeout(() => { if (!ready) disable(true, 'timeout'); }, LOAD_TIMEOUT_MS);
  }

  socket.on('expression', (data) => send({ type: 'expression', name: data?.name }));

  win.addEventListener('message', (event) => {
    if (event.origin !== origin || event.source !== frame.contentWindow) return;
    let message = {};
    try {
      message = JSON.parse(event.data);
    } catch (error) {
      return;
    }
    // the character is loaded: it shows the current expression
    if (message.type === 'ready') {
      ready = true;
      win.clearTimeout(timer);
      socket.emit('character_ready');
      onReady();
    } else if (message.type === 'failed') {
      disable(true, message.reason ?? 'failed');
    } else if (message.type === 'unmapped') {
      onUnmapped(message.presets ?? [], message.gestures ?? []);
    }
  });

  return {
    send,
    get ready() { return ready; },
    get enabled() { return enabled; },
    speaking: (value) => send({ type: 'speaking', value: Boolean(value) }),
    setInset: (inset) => send({ type: 'viewport_inset', ...inset }),
    setView: (name) => send({ type: 'view', name }),
    setBackground: (name) => send({ type: 'background', name }),
    /** the outfit variant of the workflow that answers (IF-111 `variant`); null = the chat's variant */
    setVariant: (name) => send({ type: 'variant', name: name || null }),
  };
}
