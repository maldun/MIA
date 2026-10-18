// MIA's voice. The server renders every line into its own file and tells the page that plays the voice (audio_reload: url, serial).
//  - only one page plays: the visible / used one claims the voice (audio_claim), the others are told (audio_owner) and stay silent
//  - lines are queued and played one after the other, so a line that arrives early never cuts the one that is playing
//  - the character's mouth ("talking") follows the queue: on while a line plays, off as soon as the queue is empty
// Browsers may block autoplay until the first touch/click: then a small button asks for it.

export const CLAIM_EVERY_MS = 3000;       // a page that is used claims the voice at most this often
export const HEARTBEAT_MS = 1500;         // "speaking" is repeated while a line plays (the character has a watchdog)

/** the lines that are waiting to be played */
export class LineQueue {
  constructor() {
    this.lines = [];
  }

  push(line) {
    this.lines.push(line);
  }

  /** puts a line back in front (autoplay was blocked: it is played when the user allows sound) */
  unshift(line) {
    this.lines.unshift(line);
  }

  shift() {
    return this.lines.shift();
  }

  clear() {
    this.lines = [];
  }

  get size() {
    return this.lines.length;
  }
}

/** may this page claim the voice now? (it is visible, and the last claim is not too recent) */
export function mayClaim({ visible, now, lastClaim, every = CLAIM_EVERY_MS }) {
  return Boolean(visible) && now - lastClaim >= every;
}

export function initSound({ audio, socket, character, storage, muteToggle, muteLabel, muteIcon, volume, hint, t, win = window }) {
  let muted = storage.get('mia.muted') === '1';
  let level = Math.min(100, Math.max(0, Number(storage.get('mia.volume', 100)) || 0));
  const queue = new LineQueue();
  let current = null;           // the line that is playing: {url, serial}
  let lastClaim = -Infinity;
  let first = true;
  let heartbeat = 0;

  function applyAudio() {
    audio.muted = muted;
    audio.volume = level / 100;
    muteToggle.setAttribute('aria-checked', String(muted));
    muteLabel.textContent = t(muted ? 'menu.unmute' : 'menu.mute');
    muteIcon.setAttribute('href', muted ? '#i-volume-off' : '#i-volume');
    volume.value = String(level);
  }

  // --- the character talks while a line plays or lines are waiting --------------------------------
  function speaking(value) {
    character.speaking(value);
    win.clearInterval(heartbeat);
    heartbeat = value ? win.setInterval(() => character.speaking(true), HEARTBEAT_MS) : 0;
  }

  async function startNext() {
    const line = queue.shift();
    if (!line) {
      current = null;
      speaking(false);
      return;
    }
    current = line;
    audio.src = line.url;
    try {
      await audio.play();
      hint.hidden = true;
      speaking(true);
    } catch (error) {
      if (error?.name === 'NotAllowedError') {
        // the browser wants a click first: the line waits
        queue.unshift(line);
        current = null;
        hint.hidden = false;
        speaking(false);
      } else {
        startNext();           // this line cannot be played (file gone, broken): the next one
      }
    }
  }

  function stopAll() {
    queue.clear();
    current = null;
    audio.pause();
    audio.removeAttribute('src');
    speaking(false);
  }

  audio.addEventListener('ended', () => {
    socket.emit('audio_ended', { serial: current?.serial });
    startNext();
  });
  audio.addEventListener('error', () => {
    if (current) startNext();
  });

  socket.on('audio_reload', (data) => {
    queue.push({ url: data?.url ?? '/audio/out.wav', serial: data?.serial });
    if (!current) startNext();
  });

  // --- one page plays ----------------------------------------------------------------------------------
  function claim(initial = false) {
    lastClaim = Date.now();
    socket.emit('audio_claim', { initial });
  }

  function claimIfUsed() {
    if (mayClaim({ visible: document.visibilityState === 'visible', now: Date.now(), lastClaim })) claim(false);
  }

  socket.on('audio_owner', (data) => {
    if (data?.sid && data.sid !== socket.id) stopAll();          // another page plays now
  });
  document.addEventListener('visibilitychange', claimIfUsed);
  win.addEventListener('focus', claimIfUsed);
  document.addEventListener('pointerdown', claimIfUsed, { passive: true });
  document.addEventListener('keydown', claimIfUsed, { passive: true });

  muteToggle.addEventListener('click', () => {
    muted = !muted;
    storage.set('mia.muted', muted ? '1' : '0');
    applyAudio();
  });
  volume.addEventListener('input', () => {
    level = Number(volume.value);
    storage.set('mia.volume', level);
    applyAudio();
  });
  hint.addEventListener('click', () => {
    if (!current) startNext();
  });

  applyAudio();
  return {
    refresh: applyAudio,
    /** the socket is connected: the first time a visible page also asks for the intro sound */
    connected() {
      if (document.visibilityState === 'visible') {
        claim(first);
        first = false;
      }
    },
    get queued() { return queue.size; },
    get playing() { return current !== null; },
  };
}
