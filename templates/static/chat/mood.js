// The mood line: the server decides what it says (chat_status.mood), the page shows it on every device.
// Crossfade of about 250 ms when the text changes, no flicker when it stays the same; screen readers get the new
// text at most every 30 seconds (a separate live region, not every activity change).

const FADE_MS = 125;
const ANNOUNCE_MS = 30000;

export function initMood({ chip, emoji, text, live, enabled = true, win = window, now = () => Date.now() }) {
  let shown = null;
  let lastAnnounce = 0;
  let timer = 0;

  function announce(line) {
    if (now() - lastAnnounce >= ANNOUNCE_MS) {
      lastAnnounce = now();
      live.textContent = line;
    }
  }

  function apply(mood, activity) {
    emoji.textContent = mood.emoji ?? '';
    text.textContent = mood.text ?? '';
    chip.title = mood.text ?? '';
    chip.dataset.activity = activity ?? 'idle';
    chip.dataset.emotion = mood.emotion ?? 'ready';
    chip.classList.remove('fading');
  }

  function update(mood, activity = mood?.activity) {
    if (!mood || !enabled) return;
    const key = `${mood.emoji}|${mood.text}|${activity ?? ''}`;
    if (key === shown) return;
    const first = shown === null;
    shown = key;
    announce(mood.text);
    win.clearTimeout(timer);
    if (first) {
      apply(mood, activity);
      return;
    }
    chip.classList.add('fading');
    timer = win.setTimeout(() => apply(mood, activity), FADE_MS);
  }

  chip.hidden = !enabled;
  return { update };
}
