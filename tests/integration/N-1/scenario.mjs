// Scenario of N-1 (Web Frontend): one answer from the chat page to the character and the voice (protected).
// The page receives the events of IF-101 (scripted here: the Backend is outside this node), shows the answer, tells the character the expression and
// whether it speaks (IF-111) and hands the audio lines to the voice player (IF-112). Step 0 runs it with a small stand-in page and the mocks of both
// interfaces; steps 1 to 3 swap in the Voice playback (N-1.3), the Character view (N-1.2) and the Chat and login views (N-1.1, which replace the
// stand-in page). What needs a browser (layout at 360, 768 and 1440 px, the frame rate, the request log) is decided in stage 2 and 3, not here.
import { CharacterMock } from '../../helpers/mocks/if_111_character_bridge.mjs';

export const MARKS = { 0: [], 1: ['REQ-FE-011', 'REQ-FE-012'], 2: ['REQ-FE-008', 'REQ-FE-010', 'REQ-FE-006'], 3: ['REQ-FE-001', 'REQ-FE-006'] };

const ORIGIN = 'https://mia.local';
const ANSWER = [
  { event: 'chat_message', payload: { id: 'm1', role: 'user', sender: 'anna', text: 'hi' } },
  { event: 'chat_start', payload: { id: 'm2', role: 'assistant' } },
  { event: 'expression', payload: { name: 'happy' } },
  { event: 'audio_chunk', payload: { id: 'a0', url: '/audio/a0.wav', index: 0, sentence: 'Hello Anna.' } },
  { event: 'audio_chunk', payload: { id: 'a1', url: '/audio/a1.wav', index: 1, sentence: 'How are you?' } },
  { event: 'chat_done', payload: { id: 'm2', text: 'Hello Anna. How are you?', status: 'done', emotion: 'happy' } },
];

/** the stand-in for the chat page of N-1.1: what the page does with the events of IF-101 */
export function standInPage(character, voice) {
  const shown = [];
  const toCharacter = (message) => character.receive(JSON.stringify(message), ORIGIN);
  voice.onSpeaking((value) => toCharacter({ type: 'speaking', value }));
  return {
    shown,
    handle({ event, payload }) {
      if (event === 'chat_message' || event === 'chat_done') shown.push(payload.text);
      if (event === 'expression') toCharacter({ type: 'expression', name: payload.name });
      if (event === 'audio_chunk') voice.enqueue({ id: payload.id, url: payload.url, serial: payload.index });
    },
  };
}

export function run(p, assert) {
  const character = p['IF-111'];
  const voice = p['IF-112'];
  const page = p.page ?? standInPage(character, voice);

  // the character loads and says so; the page sees the answer, the expression and the speaking signal in order
  character.load();
  assert.equal(JSON.parse(character.outbox[0]).type, 'ready');
  ANSWER.forEach((e) => page.handle(e));
  assert.equal(character.state.expression, 'happy');
  voice.tick();
  assert.equal(character.state.speaking, true);
  voice.tick();
  assert.deepEqual(voice.played, ['a0', 'a1']);
  assert.equal(character.state.speaking, false);

  // an unknown mood shows neutral and breaks nothing
  page.handle({ event: 'expression', payload: { name: 'no-such-mood' } });
  assert.equal(character.state.expression, 'neutral');

  // this device is muted: nothing plays, the chat still shows the answer
  voice.mute(true);
  ANSWER.forEach((e) => page.handle(e));
  voice.tick();
  assert.deepEqual(voice.played, ['a0', 'a1']);

  // the character cannot load (no WebGL): the page still shows and speaks (the chat does not depend on the character)
  const blocked = new CharacterMock({ loads: false });
  const plain = standInPage(blocked, voice);
  voice.mute(false);
  blocked.load();
  assert.equal(JSON.parse(blocked.outbox[0]).type, 'failed');
  plain.handle(ANSWER[3]);
  voice.tick();
  assert.equal(voice.played.at(-1), 'a0');
  plain.handle(ANSWER[5]);
  assert.deepEqual(plain.shown, ['Hello Anna. How are you?']);
}
