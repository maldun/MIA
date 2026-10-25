// Mock of IF-112, the voice player (protected). Complexity 3: a queue with a clock and a blocked-autoplay state.
// It plays no sound; tick() lets the player finish one line.
export class VoicePlayerMock {
  constructor() {
    this.queue = [];
    this.played = [];
    this.muted = false;
    this.owner = true;
    this.blocked = false;
    this.speaking = false;
    this.claims = 0;
    this.speakingCb = () => {};
    this.onBlocked = () => {};
    this.onLineError = () => {};
  }

  onSpeaking(callback) { this.speakingCb = callback; }
  enqueue(line) { if (!this.muted) this.queue.push(line); }
  mute(value) { this.muted = Boolean(value); if (this.muted) this.queue = []; }
  claim() { this.claims += 1; }
  setOwner(value) { this.owner = Boolean(value); }
  allowAutoplay() { this.blocked = false; }
  stop() { this.queue = []; this._speaking(false); }

  _speaking(value) { if (this.speaking !== value) { this.speaking = value; this.speakingCb(value); } }

  /** test adapter: the player finishes one line (or reports what keeps it from playing) */
  tick() {
    if (!this.queue.length) { this._speaking(false); return; }
    if (this.blocked) { this.onBlocked(this.queue[0]); return; }
    const line = this.queue.shift();
    if (!this.owner) return;                              // a page that is not the owner stays silent
    if (line.fail) { this.onLineError(line.id); } else { this.played.push(line.id); this._speaking(true); }
    if (!this.queue.length) this._speaking(false);
  }
}
