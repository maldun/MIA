// The 3D character lives in an iframe (same origin). Messages are JSON strings (postMessage), see ui/README.md.

export function initCharacter({ frame, socket, origin = location.origin, enabled = true }) {
  function send(message) {
    if (enabled && frame.contentWindow) frame.contentWindow.postMessage(JSON.stringify(message), origin);
  }

  if (!enabled) {
    frame.removeAttribute('src');
    frame.hidden = true;
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
    if (message.type === 'ready') socket.emit('character_ready');
  });

  return { send, speaking: (value) => send({ type: 'speaking', value: Boolean(value) }) };
}
