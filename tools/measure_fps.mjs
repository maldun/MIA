// Frame rate of the character (REQ-EVL-007, benchmark BM-MIA-002): the median of the frame times, as frames per second.
//   node tools/measure_fps.mjs frames.json        frames.json = a list of frame times in milliseconds (recorded in the browser, e.g. with
//                                                 requestAnimationFrame timestamps: differences of consecutive timestamps)
// The median, not the mean: one long frame (a page load, a garbage collection) must not decide the result.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export function fpsOf(frameTimesMs) {
  if (!Array.isArray(frameTimesMs) || frameTimesMs.length === 0) throw new Error('no frame times');
  const sorted = [...frameTimesMs].sort((a, b) => a - b);
  const middle = sorted.length >> 1;
  const median = sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  return 1000 / median;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const times = JSON.parse(readFileSync(process.argv[2], 'utf8'));
  console.log(JSON.stringify({ frames: times.length, fps: Math.round(fpsOf(times) * 10) / 10 }));
}
