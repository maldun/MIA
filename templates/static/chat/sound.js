// MIA's voice. The server renders every line into its own file and tells the page that plays the voice (audio_reload: url, serial).
//  - only one page plays: the visible / used one claims the voice (audio_claim), the others are told (audio_owner) and stay silent
//  - lines are queued and played one after the other, so a line that arrives early never cuts the one that is playing
//  - the character's mouth ("talking") follows the queue: on while a line plays, off as soon as the queue is empty
// Browsers may block autoplay until the first touch/click: then a small button asks for it.
// VoicePlayer is the interface IF-112 (contracts/IF-112-voice-player.md): the queue, the claim, mute and stop. initSound ties it to the page.

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

/**
 * Plays lines one after the other on one audio element (IF-112, REQ-VPB-001 to REQ-VPB-003).
 * Muting silences this device only: the lines still run (without sound), so the character and the server keep in step.
 */
export class VoicePlayer {
  constructor({ audio, onEnded = () => {}, emitClaim = () => {}, clock = Date.now }) {
    this.audio = audio;
    this.queue = new LineQueue();
    this.current = null;                // the line that is playing: {id, url, serial}
    this.owner = true;                  // the page that was told to play; another page stays silent
    this.onBlocked = () => {};          // (line) autoplay was refused: the line waits for allowAutoplay()
    this.onLineError = () => {};        // (id) a line could not be played: it is skipped
    this._onEnded = onEnded;
    this._emitClaim = emitClaim;
    this._clock = clock;
    this._lastClaim = -Infinity;
    this._held = false;                 // autoplay was refused: lines wait until allowAutoplay()
    this._speaking = false;
    this._speakingCallback = () => {};
    audio.addEventListener('ended', () => {
      this._onEnded(this.current);
      this._startNext();
    });
    audio.addEventListener('error', () => {
      if (!this.current) return;
      this.onLineError(this.current.id);
      this._startNext();
    });
  }

  /** callback(bool): true when the first line starts, false when nothing is left to play */
  onSpeaking(callback) {
    this._speakingCallback = callback;
  }

  enqueue(line) {
    if (!this.owner) return;
    this.queue.push(line);
    if (!this.current && !this._held) this._startNext();      // held: the browser refused autoplay, nothing is tried before allowAutoplay()
  }

  mute(value) {
    this.audio.muted = Boolean(value);
  }

  /** ends the playing line and clears the queue */
  stop() {
    this.queue.clear();
    this.current = null;
    this._held = false;
    this.audio.pause();
    this.audio.removeAttribute('src');
    this._setSpeaking(false);
  }

  /** the answer to claim(): a page that is not the owner stays silent and drops what it has */
  setOwner(value) {
    this.owner = Boolean(value);
    if (!this.owner) this.stop();
  }

  /** after a user gesture: plays the line that was held back */
  allowAutoplay() {
    this._held = false;
    if (!this.current) this._startNext();
  }

  /** asks to be the page that plays; without force at most every CLAIM_EVERY_MS */
  claim({ initial = false, force = false } = {}) {
    const now = this._clock();
    if (!force && !mayClaim({ visible: true, now, lastClaim: this._lastClaim })) return;
    this._lastClaim = now;
    this._emitClaim({ initial });
  }

  /** a page that is used (visible, touched) claims the voice if it has not done so lately */
  claimIfUsed(visible) {
    if (mayClaim({ visible, now: this._clock(), lastClaim: this._lastClaim })) this.claim({ force: true });
  }

  get queued() { return this.queue.size; }

  get playing() { return this.current !== null; }

  _setSpeaking(value) {
    if (value === this._speaking) return;
    this._speaking = value;
    this._speakingCallback(value);
  }

  _startNext() {
    const line = this.queue.shift();
    if (!line) {
      this.current = null;
      this._setSpeaking(false);
      return;
    }
    this.current = line;
    this.audio.src = line.url;
    let started;
    try {
      started = this.audio.play();
    } catch (error) {
      this._notStarted(line, error);
      return;
    }
    // a browser answers with a promise; an element that plays at once (a test double) is taken as started
    if (started && typeof started.then === 'function') started.then(() => this._setSpeaking(true), (error) => this._notStarted(line, error));
    else this._setSpeaking(true);
  }

  _notStarted(line, error) {
    if (error?.name === 'NotAllowedError') {
      // the browser wants a click first: the line waits at the front
      this.queue.unshift(line);
      this.current = null;
      this._held = true;
      this._setSpeaking(false);
      this.onBlocked(line);
    } else {
      this.onLineError(line.id);
      this._startNext();                 // this line cannot be played (file gone, broken): the next one
    }
  }
}

export function initSound({ audio, socket, character, storage, muteToggle, muteLabel, muteIcon, volume, hint, t, win = window }) {
  let muted = storage.get('mia.muted') === '1';
  let level = Math.min(100, Math.max(0, Number(storage.get('mia.volume', 100)) || 0));
  let first = true;
  let heartbeat = 0;

  // --- the character talks while a line plays or lines are waiting --------------------------------
  function speaking(value) {
    character.speaking(value);
    win.clearInterval(heartbeat);
    heartbeat = value ? win.setInterval(() => character.speaking(true), HEARTBEAT_MS) : 0;
    if (value) hint.hidden = true;
  }

  const player = new VoicePlayer({
    audio,
    onEnded: (line) => socket.emit('audio_ended', { serial: line?.serial }),
    emitClaim: (data) => socket.emit('audio_claim', data),
  });
  player.onSpeaking(speaking);
  player.onBlocked = () => { hint.hidden = false; };

  function applyAudio() {
    player.mute(muted);
    audio.volume = level / 100;
    muteToggle.setAttribute('aria-checked', String(muted));
    muteLabel.textContent = t(muted ? 'menu.unmute' : 'menu.mute');
    muteIcon.setAttribute('href', muted ? '#i-volume-off' : '#i-volume');
    volume.value = String(level);
  }

  socket.on('audio_reload', (data) => {
    player.enqueue({ url: data?.url ?? '/audio/out.wav', serial: data?.serial });
  });

  // --- one page plays ----------------------------------------------------------------------------------
  const claimIfUsed = () => player.claimIfUsed(document.visibilityState === 'visible');

  socket.on('audio_owner', (data) => {
    if (data?.sid) player.setOwner(data.sid === socket.id);          // another page plays now, or this one again
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
  hint.addEventListener('click', () => player.allowAutoplay());

  applyAudio();
  return {
    refresh: applyAudio,
    /** the socket is connected: the first time a visible page also asks for the intro sound */
    connected() {
      if (document.visibilityState === 'visible') {
        player.claim({ initial: first, force: true });
        first = false;
      }
    },
    get queued() { return player.queued; },
    get playing() { return player.playing; },
  };
}
