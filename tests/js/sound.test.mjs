// The queue of voice lines and the rule for claiming the voice: node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { LineQueue, mayClaim, CLAIM_EVERY_MS, HEARTBEAT_MS } from '../../templates/static/chat/sound.js';

test('lines are played in the order they arrive', () => {
  const queue = new LineQueue();
  queue.push({ url: '/audio/a.wav', serial: 1 });
  queue.push({ url: '/audio/b.wav', serial: 2 });
  queue.push({ url: '/audio/c.wav', serial: 3 });
  assert.equal(queue.size, 3);
  assert.deepEqual(queue.shift().serial, 1);
  assert.deepEqual(queue.shift().serial, 2);
  assert.deepEqual(queue.shift().serial, 3);
  assert.equal(queue.shift(), undefined);
  assert.equal(queue.size, 0);
});

test('a line that could not start (autoplay blocked) goes back to the front', () => {
  const queue = new LineQueue();
  queue.push({ serial: 1 });
  queue.push({ serial: 2 });
  const blocked = queue.shift();
  queue.unshift(blocked);
  assert.equal(queue.shift().serial, 1);
  assert.equal(queue.shift().serial, 2);
});

test('clearing forgets everything that was waiting', () => {
  const queue = new LineQueue();
  queue.push({ serial: 1 });
  queue.push({ serial: 2 });
  queue.clear();
  assert.equal(queue.size, 0);
  assert.equal(queue.shift(), undefined);
});

test('only a visible page may claim the voice, and not too often', () => {
  assert.equal(mayClaim({ visible: true, now: 10000, lastClaim: -Infinity }), true);
  assert.equal(mayClaim({ visible: false, now: 10000, lastClaim: -Infinity }), false);
  assert.equal(mayClaim({ visible: true, now: 10000, lastClaim: 10000 - CLAIM_EVERY_MS + 1 }), false);
  assert.equal(mayClaim({ visible: true, now: 10000, lastClaim: 10000 - CLAIM_EVERY_MS }), true);
});

test('the heartbeat is faster than the watchdog of the character (5 s)', () => {
  assert.ok(HEARTBEAT_MS < 5000 / 2);
});
