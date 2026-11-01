// The real provider of IF-112 for the contract suite and the integration steps (protected, amendment A-72): the VoicePlayer of N-1.3 on an
// audio element that answers at once, with the test adapter of the mock (tick, played) added. It plays no sound.
// tick() lets the line that plays finish (the `ended` event), so the next one starts; the mock has the same meaning ("the player finishes one line").
import { VoicePlayer } from '../../../templates/static/chat/sound.js';

/** an audio element that plays at once (VoicePlayer takes an answer without a promise as started); it can refuse autoplay and fail on chosen files */
class ImmediateAudio {
  constructor() {
    this.src = '';
    this.muted = false;
    this.volume = 1;
    this.blocked = false;
    this.failing = new Set();
    this.listeners = {};
  }

  addEventListener(name, fn) { (this.listeners[name] ||= []).push(fn); }
  removeAttribute() { this.src = ''; }
  pause() {}

  play() {
    if (this.blocked) { const error = new Error('blocked'); error.name = 'NotAllowedError'; throw error; }
    if (this.failing.has(this.src)) throw new Error('file gone');
  }

  fire(name) { (this.listeners[name] || []).forEach((fn) => fn()); }
}

export class RealVoicePlayer {
  constructor() {
    this.played = [];
    this.audio = new ImmediateAudio();
    this.claims = 0;
    this.player = new VoicePlayer({
      audio: this.audio,
      onEnded: (line) => { if (line) this.played.push(line.id); },
      emitClaim: () => { this.claims += 1; },
    });
  }

  get muted() { return this.audio.muted; }
  get owner() { return this.player.owner; }
  get speaking() { return this.player._speaking; }
  get queue() { return this.player.queue.lines; }
  get blocked() { return this.audio.blocked; }
  set blocked(value) { this.audio.blocked = Boolean(value); }
  get onBlocked() { return this.player.onBlocked; }
  set onBlocked(fn) { this.player.onBlocked = fn; }
  get onLineError() { return this.player.onLineError; }
  set onLineError(fn) { this.player.onLineError = fn; }

  onSpeaking(callback) { this.player.onSpeaking(callback); }
  enqueue(line) { if (line.fail) this.audio.failing.add(line.url); this.player.enqueue(line); }
  mute(value) { this.player.mute(value); }
  claim() { this.player.claim({ force: true }); }
  setOwner(value) { this.player.setOwner(value); }
  allowAutoplay() { this.audio.blocked = false; this.player.allowAutoplay(); }
  stop() { this.player.stop(); }

  /** test adapter: the playing line ends; the next one starts, or the voice goes quiet */
  tick() { if (this.player.playing) this.audio.fire('ended'); }
}
