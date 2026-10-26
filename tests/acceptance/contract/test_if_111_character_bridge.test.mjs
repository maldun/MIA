// IF-111 character bridge (Chat and login views to Character view): the contract suite runs against the mock (stage 1) and the real
// Character view (stage 2, skipped until N-1.2 is integrated). Protected after the Plan gate.
// Run with: node --test "tests/acceptance/contract/test_if_111_character_bridge.test.mjs"
import assert from 'node:assert/strict';
import { eachProvider } from '../../helpers/contract.mjs';
import { CharacterMock } from '../../helpers/mocks/if_111_character_bridge.mjs';

const ORIGIN = 'https://mia.local';
const make = (options = {}) => (kind) => (kind === 'mock' ? new CharacterMock({ origin: ORIGIN, ...options }) : null);
const send = (character, message, origin = ORIGIN) => character.receive(JSON.stringify(message), origin);

// mark.req("IF-111", "REQ-FE-008")
eachProvider('IF-111', 'TC-IF-111-01 golden 1: after ready, an expression and the mouth follow the messages', make(), (character) => {
  const heard = [];
  character.onMessage((text) => heard.push(JSON.parse(text)));
  character.load();
  assert.deepEqual(heard, [{ type: 'ready' }]);
  send(character, { type: 'expression', name: 'happy' });
  send(character, { type: 'speaking', value: true });
  assert.equal(character.state.expression, 'happy');
  assert.equal(character.state.speaking, true);
  send(character, { type: 'speaking', value: false });
  assert.equal(character.state.speaking, false);
});

// mark.req("IF-111", "REQ-FE-010")
eachProvider('IF-111', 'TC-IF-111-02 golden 3: an unknown expression keeps the current one', make(), (character) => {
  send(character, { type: 'expression', name: 'happy' });
  send(character, { type: 'expression', name: 'nonsense' });
  assert.equal(character.state.expression, 'happy');
});

// mark.req("IF-111")
eachProvider('IF-111', 'TC-IF-111-03 golden 3: a foreign origin, malformed JSON and an unknown type change nothing and raise nothing', make(), (character) => {
  send(character, { type: 'expression', name: 'sad' });
  send(character, { type: 'expression', name: 'happy' }, 'https://evil.example');
  character.receive('{not json', ORIGIN);
  character.receive('42', ORIGIN);
  send(character, { type: 'launch_missiles' });
  assert.equal(character.state.expression, 'sad');
});

// mark.req("IF-111", "REQ-FE-007")
eachProvider('IF-111', 'TC-IF-111-04 golden 3: the covered area counts negative or missing values as 0', make(), (character) => {
  send(character, { type: 'viewport_inset', left: -5, right: 432, top: 58, bottom: 0, width: 1440, height: 900 });
  assert.deepEqual(character.state.inset, { left: 0, right: 432, top: 58, bottom: 0, width: 1440, height: 900 });
  send(character, { type: 'viewport_inset', right: 10 });
  assert.equal(character.state.inset.left, 0);
});

// mark.req("IF-111", "REQ-FE-006")
eachProvider('IF-111', 'TC-IF-111-05 golden 2: a character that cannot load says failed once', make({ loads: false }), (character) => {
  const heard = [];
  character.onMessage((text) => heard.push(JSON.parse(text)));
  character.load();
  assert.equal(heard.length, 1);
  assert.equal(heard[0].type, 'failed');
  send(character, { type: 'expression', name: 'happy' });     // later messages raise nothing
});

// mark.req("IF-111", "REQ-FE-020", "REQ-FE-021")
eachProvider('IF-111', 'TC-IF-111-06: a model that cannot map everything reports what is missing; a variant and null', make(), (character) => {
  const heard = [];
  character.onMessage((text) => heard.push(JSON.parse(text)));
  send(character, { type: 'model', name: 'B' });
  assert.deepEqual(heard.at(-1), { type: 'unmapped', presets: ['wink'], gestures: ['bow'] });
  send(character, { type: 'model', name: 'A' });
  assert.deepEqual(heard.at(-1), { type: 'unmapped', presets: [], gestures: [] });
  send(character, { type: 'variant', name: 'summer' });
  assert.equal(character.state.variant, 'summer');
  send(character, { type: 'variant', name: null });
  assert.equal(character.state.variant, null);
});
