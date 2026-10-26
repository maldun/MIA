// Pure helpers of the views that IF-101 v1 added (answer actions, votes, records, trust, variant). No DOM, so node tests them (tests/js/panels.test.mjs).

export const VOTE_CATEGORIES = ['answer_quality', 'reactions', 'character_behaviour', 'service'];
export const ITEM_KINDS = ['tasks', 'memos', 'memory'];

/** the id of the answer that "regenerate" is offered on: the last answer that is written and stored (IF-101: only the last one) */
export function lastAnswerId(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const m = messages[i];
    if (m.role === 'assistant') return m.text && !m.streaming && !m.local && !String(m.id).startsWith('~') ? m.id : null;
  }
  return null;
}

/** the vote on an answer: the category is answer_quality, the value 1 (plus) or -1 (minus) */
export function voteArgs(message, value) {
  if (value !== 1 && value !== -1) throw new Error('a vote is 1 or -1');
  return { subject: message.id, category: 'answer_quality', value };
}

/** the score as lines to draw: overall first, then the four categories in a fixed order (a category without votes shows 0) */
export function scoreLines(score, t) {
  const categories = score?.categories ?? {};
  return [
    { key: 'overall', label: t('vote.overall'), value: score?.overall ?? 0 },
    ...VOTE_CATEGORIES.map((key) => ({ key, label: t(`vote.category.${key}`), value: categories[key] ?? 0 })),
  ];
}

/** what is wrong with a record before it is sent: 'empty' (no text), 'source' (memory without a source), or null */
export function itemDraftError(kind, text, source = null) {
  if (typeof text !== 'string' || !text.trim()) return 'empty';
  if (kind === 'memory' && !(typeof source === 'string' && source.trim())) return 'source';
  return null;
}

/** the trust value typed by a person: 0 to 1 (a decimal comma is accepted); anything else is null */
export function parseTrust(input) {
  if (typeof input !== 'string' || !input.trim()) return null;
  const value = Number(input.trim().replace(',', '.'));
  return Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;
}

export const MIN_PASSWORD = 8;

/** what is wrong with the typed passwords before they are sent: 'empty', 'short', 'mismatch', 'same', or null (REQ-BE-011: at least 8 characters) */
export function passwordProblem(oldPassword, newPassword, repeat) {
  if (!oldPassword || !newPassword) return 'empty';
  if (newPassword.length < MIN_PASSWORD) return 'short';
  if (newPassword !== repeat) return 'mismatch';
  if (newPassword === oldPassword) return 'same';
  return null;
}

/** the small label with the variant name while a workflow with a character variant runs */
export function variantLabel(name, t) {
  return name ? t('variant.label', { name }) : '';
}
