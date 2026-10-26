// IF-112 voice player (Chat and login views to Voice playback): the contract suite runs against the mock (stage 1) and the real
// Voice playback (stage 2, skipped until N-1.3 is integrated). Protected after the Plan gate.
// Run with: node --test "tests/acceptance/contract/test_if_112_voice_player.test.mjs"
import assert from 'node:assert/strict';
import { eachProvider } from '../../helpers/contract.mjs';
import { VoicePlayerMock } from '../../helpers/mocks/if_112_voice_player.mjs';

const make = (kind) => (kind === 'mock' ? new VoicePlayerMock() : null);
const line = (id, extra = {}) => ({ id, url: `/audio/${id}.wav`, serial: 1, ...extra });
const watch = (player) => { const seen = []; player.onSpeaking((v) => seen.push(v)); return seen; };

// mark.req("IF-112", "REQ-FE-011")
eachProvider('IF-112', 'TC-IF-112-01 golden 1: lines play in arrival order and the speaking signal is true once and false once', make, (player) => {
  const seen = watch(player);
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id)));
  player.tick(); player.tick(); player.tick();
  assert.deepEqual(player.played, ['a', 'b', 'c']);
  assert.deepEqual(seen, [true, false]);
});

// mark.req("IF-112", "REQ-FE-011")
eachProvider('IF-112', 'TC-IF-112-02: a line that arrives early never cuts the playing one', make, (player) => {
  player.enqueue(line('a'));
  player.enqueue(line('b'));
  player.tick();
  player.enqueue(line('c'));
  player.tick(); player.tick();
  assert.deepEqual(player.played, ['a', 'b', 'c']);
});

// mark.req("IF-112", "REQ-FE-012")
eachProvider('IF-112', 'TC-IF-112-03 golden 2: a muted device plays nothing and a second device still plays', make, (muted) => {
  const other = make('mock');
  muted.mute(true);
  muted.enqueue(line('a'));
  other.enqueue(line('a'));
  muted.tick(); other.tick();
  assert.deepEqual(muted.played, []);
  assert.deepEqual(other.played, ['a']);
});

// mark.req("IF-112", "REQ-FE-012")
eachProvider('IF-112', 'TC-IF-112-04: stop clears the queue and ends speaking; a page that is not the owner stays silent', make, (player) => {
  const seen = watch(player);
  player.enqueue(line('a')); player.enqueue(line('b')); player.enqueue(line('c'));
  player.tick();
  player.stop();
  player.tick();
  assert.deepEqual(player.played, ['a']);
  assert.equal(seen.at(-1), false);
  player.setOwner(false);
  player.enqueue(line('d'));
  player.tick();
  assert.deepEqual(player.played, ['a']);
});

// mark.req("IF-112", "REQ-FE-011")
eachProvider('IF-112', 'TC-IF-112-05 golden 3: blocked autoplay holds the lines and nothing is lost; a line that cannot load is skipped', make, (player) => {
  const blocked = [];
  const failed = [];
  player.onBlocked = (l) => blocked.push(l.id);
  player.onLineError = (id) => failed.push(id);
  player.blocked = true;
  ['a', 'b', 'c'].forEach((id) => player.enqueue(line(id, id === 'b' ? { fail: true } : {})));
  player.tick();
  assert.deepEqual(blocked, ['a']);
  assert.deepEqual(player.played, []);
  player.allowAutoplay();
  player.tick(); player.tick(); player.tick();
  assert.deepEqual(player.played, ['a', 'c']);
  assert.deepEqual(failed, ['b']);
});
