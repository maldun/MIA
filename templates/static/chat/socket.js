// Connection to the server (socket.io, vendored). The server is the one that served the page.
import { io } from '../vendor/socket.io.esm.min.js';

export function connect(onState, origin = location.origin) {
  const socket = io(origin, { reconnectionDelayMax: 10000 });
  onState('connecting');
  socket.on('connect', () => onState('online'));
  socket.on('disconnect', () => onState('offline'));
  socket.on('connect_error', () => onState('offline'));
  socket.io.on('reconnect_attempt', () => onState('reconnecting'));
  return socket;
}
