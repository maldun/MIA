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
 * onReady: the character loaded (send it the current view and inset); onFailed: no WebGL or no answer in time, the chat
 * then works full width and the page shows a small notice.
 */
export function initCharacter({ frame, socket, origin = location.origin, enabled = true, onReady = () => {}, onFailed = () => {}, win = window }) {
  let ready = false;
  let timer = 0;

  function send(message) {
    if (enabled && frame.contentWindow) frame.contentWindow.postMessage(JSON.stringify(message), origin);
  }

  function disable(failed) {
    enabled = false;
    frame.removeAttribute('src');
    frame.hidden = true;
    win.clearTimeout(timer);
    if (failed) onFailed();
  }

  if (!enabled) {
    disable(false);
  } else if (!webglAvailable()) {
    disable(true);
  } else {
    timer = win.setTimeout(() => { if (!ready) disable(true); }, LOAD_TIMEOUT_MS);
  }

  socket.on('expression', (data) => send({ type: 'expression', name: data?.name }));

  window.addEventListener('message', (event) => {
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
  };
}
