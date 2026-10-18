// Pure helpers of the conversation: ordering, grouping, times, links, commands. No DOM here, so node can test them
// (tests/js/chat.test.mjs).

export const GROUP_MINUTES = 5;
export const MAX_IN_DOM = 300;

export const EMOJI = {
  neutral: '😊', happy: '😄', mia: '👋', agree: '👍', disagree: '🙅', annoyed: '😒', sad: '😢',
  angry: '😠', surprised: '😮', embarrassed: '😳', smug: '😏', thinking: '🤔',
};

export function emojiFor(emotion) {
  return emotion ? EMOJI[String(emotion).toLowerCase()] ?? EMOJI.neutral : '';
}

/** inserts into a list sorted by id; a message with the same id (or the same client id) is replaced. Returns the index. */
export function upsert(list, message) {
  let index = list.findIndex((m) => m.id === message.id);
  if (index < 0 && message.client_id) index = list.findIndex((m) => m.client_id === message.client_id);
  if (index >= 0) {
    list[index] = { ...list[index], ...message };
    return index;
  }
  let at = list.length;
  while (at > 0 && String(list[at - 1].id) > String(message.id)) at -= 1;
  list.splice(at, 0, message);
  return at;
}

/** the oldest messages go when the list is longer than the window; returns the removed ones */
export function trimOldest(list, max = MAX_IN_DOM) {
  return list.length > max ? list.splice(0, list.length - max) : [];
}

function minutesBetween(a, b) {
  return Math.abs(new Date(a).getTime() - new Date(b).getTime()) / 60000;
}

/** a message continues the group of the previous one: same sender, close in time, no system notes */
export function continuesGroup(previous, message) {
  if (!previous || previous.role !== message.role || message.role === 'system') return false;
  if (Boolean(previous.auto) !== Boolean(message.auto)) return false;
  return minutesBetween(previous.created, message.created) <= GROUP_MINUTES;
}

export function dayKey(iso) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function dayLabel(iso, now, t, locale = undefined) {
  const today = dayKey(now);
  const yesterday = dayKey(new Date(new Date(now).getTime() - 86400000));
  const key = dayKey(iso);
  if (key === today) return t('time.today');
  if (key === yesterday) return t('time.yesterday');
  return new Date(iso).toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' });
}

export function clock(iso, locale = undefined) {
  return new Date(iso).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
}

/** "now", "5 min ago", then the time of day */
export function relativeTime(iso, now, t, locale = undefined) {
  const seconds = (new Date(now).getTime() - new Date(iso).getTime()) / 1000;
  if (seconds < 45) return t('time.now');
  if (seconds < 3600) return t('time.minutes', { n: Math.max(1, Math.round(seconds / 60)) });
  return clock(iso, locale);
}

const URL_PATTERN = /https?:\/\/[^\s<>"']+[^\s<>"'.,;:!?)\]]/g;

/** splits typed text into plain parts and links ({text} | {href}) so the page can build the nodes safely */
export function linkify(text) {
  const parts = [];
  let last = 0;
  for (const match of text.matchAll(URL_PATTERN)) {
    if (match.index > last) parts.push({ text: text.slice(last, match.index) });
    parts.push({ href: match[0] });
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last) });
  return parts;
}

/** commands that start with what was typed ("/" shows all); only while the text is a single word starting with / */
export function filterCommands(commands, typed) {
  if (!typed.startsWith('/') || /\s/.test(typed)) return [];
  const wanted = typed.toLowerCase();
  return commands.filter((c) => c.command.startsWith(wanted));
}

export function modelLabel(profile) {
  return profile === 'light' ? 'light' : profile === 'full' ? 'full' : '';
}
