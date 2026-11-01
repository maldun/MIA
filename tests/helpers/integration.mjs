// ports(real) and need(nodes): the subjects of an integration step of the Web Frontend (protected).
// A step runs the scenario of its node with the parts integrated so far real and all others as mocks (decomposition.yaml, `integration`).
// need(nodes) gives the reason to skip a step until every node it needs is in READY. The integration of a node adds it to READY and gives
// realSubject() its adapter; both edits are amendments of this protected file, made with the owner.
import { CharacterMock } from './mocks/if_111_character_bridge.mjs';
import { VoicePlayerMock } from './mocks/if_112_voice_player.mjs';
import { RealVoicePlayer } from './real/if_112_voice_player.mjs';

export const READY = new Set(['N-1.3', 'N-1.2', 'N-1.1']);    // nodes whose integration step has been done (A-72: the Voice playback; A-73: the Character view; A-74: the Chat and login views)

export function need(nodes) {
  const missing = nodes.filter((n) => !READY.has(n));
  return missing.length ? `${missing.join(', ')} not integrated yet` : null;
}

function realSubject(iface) {
  if (iface === 'IF-112') return new RealVoicePlayer();     // A-72: the Voice playback N-1.3
  // A-73 (D-175): the real Character view is Godot; its bridge is checked by ui/godot/tools/test_bridge.gd, not inside this scenario
  if (iface === 'IF-111') return new CharacterMock();
  throw new Error(`the real adapter of ${iface} is added by the integration step of its node`);
}

const MOCKS = { 'IF-111': () => new CharacterMock(), 'IF-112': () => new VoicePlayerMock() };

export function ports(real = []) {
  const out = {};
  for (const iface of Object.keys(MOCKS)) out[iface] = real.includes(iface) ? realSubject(iface) : MOCKS[iface]();
  return out;
}
