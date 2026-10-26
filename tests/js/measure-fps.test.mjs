// TC-EVL-007 (N-4.1 T-05): the frame-rate tool on recorded lists of frame times.  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { fpsOf } from '../../tools/measure_fps.mjs';

test('TC-EVL-007: 16.7 ms frames are 60 fps and 33.3 ms frames are 30 fps (within 1)', () => {
  assert.ok(Math.abs(fpsOf(Array(100).fill(16.7)) - 60) <= 1);
  assert.ok(Math.abs(fpsOf(Array(100).fill(33.3)) - 30) <= 1);
});

test('TC-EVL-007: the median decides, one long frame does not', () => {
  const times = Array(99).fill(16.7).concat([500]);
  assert.ok(Math.abs(fpsOf(times) - 60) <= 1);
});

test('TC-EVL-007: no frames is an error, not 0 fps', () => {
  assert.throws(() => fpsOf([]));
});
