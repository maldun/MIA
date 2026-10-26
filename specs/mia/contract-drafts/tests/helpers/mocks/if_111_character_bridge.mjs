// Mock of IF-111, the character bridge (protected). Complexity 2: a fake character that keeps the last state it was told.
// It draws nothing and knows no real shape keys: the models and what they cannot map are scripted below.
const PRESETS = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'shocked'];
const MODELS = { A: { presets: [], gestures: [] }, B: { presets: ['wink'], gestures: ['bow'] } };
const clamp = (n) => (Number.isFinite(n) && n > 0 ? n : 0);

export class CharacterMock {
  constructor({ origin = 'https://mia.local', loads = true } = {}) {
    this.origin = origin;
    this.loads = loads;
    this.state = { expression: 'neutral', speaking: false, inset: { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 }, view: null, background: null, variant: null, model: null };
    this.outbox = [];
    this.listener = () => {};
  }

  onMessage(callback) { this.listener = callback; }

  say(message) { const text = JSON.stringify(message); this.outbox.push(text); this.listener(text); }

  /** the iframe finished loading */
  load() { if (this.loads) this.say({ type: 'ready' }); else this.say({ type: 'failed', reason: 'no WebGL' }); }

  /** a message from the page: a JSON string and the origin it came from */
  receive(data, origin) {
    if (origin !== this.origin) return;
    let message;
    try { message = JSON.parse(data); } catch (error) { return; }
    if (!message || typeof message !== 'object') return;
    const s = this.state;
    switch (message.type) {
      case 'expression': if (PRESETS.includes(message.name)) s.expression = message.name; break;   // A-04: an unknown name keeps the current one
      case 'speaking': s.speaking = Boolean(message.value); break;
      case 'viewport_inset': for (const key of Object.keys(s.inset)) s.inset[key] = clamp(message[key]); break;
      case 'view': s.view = message.name ?? null; break;
      case 'background': s.background = message.name ?? null; break;
      case 'variant': s.variant = message.name ?? null; break;
      case 'model':
        s.model = message.name;
        this.say({ type: 'unmapped', ...(MODELS[message.name] || { presets: [], gestures: [] }) });
        break;
      default: break;                                   // an unknown type is ignored
    }
  }
}
