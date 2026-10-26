// The logic of the views of N-1.1 that needs no DOM: which answer can be regenerated, the vote, the score lines, record drafts, trust input, the variant label.
// TC-CLV-005, -008, -010, -011, -012, -013.  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { VOTE_CATEGORIES, itemDraftError, lastAnswerId, parseTrust, passwordProblem, scoreLines, variantLabel, voteArgs } from '../../templates/static/chat/panels-model.js';

const t = (key, vars = {}) => `${key}${Object.keys(vars).length ? JSON.stringify(vars) : ''}`;

test('TC-CLV-005: only the last answer with text can be regenerated', () => {
  const messages = [{ id: 'm1', role: 'user', text: 'hi' }, { id: 'm2', role: 'assistant', text: 'hello' }, { id: 'm3', role: 'user', text: 'again' }];
  assert.equal(lastAnswerId(messages), 'm2');
  assert.equal(lastAnswerId([{ id: 'm1', role: 'user', text: 'hi' }]), null);
  assert.equal(lastAnswerId([{ id: 'm2', role: 'assistant', text: '', streaming: true }]), null);                 // still being written
  assert.equal(lastAnswerId([{ id: 'm2', role: 'assistant', text: 'a' }, { id: 'm4', role: 'assistant', text: 'b' }]), 'm4');
  assert.equal(lastAnswerId([{ id: '~1', role: 'assistant', text: 'a', local: 'sending' }]), null);
});

test('TC-CLV-010: a vote on an answer has the subject, the category answer_quality and the value', () => {
  assert.deepEqual(voteArgs({ id: 'm2' }, 1), { subject: 'm2', category: 'answer_quality', value: 1 });
  assert.deepEqual(voteArgs({ id: 'm2' }, -1), { subject: 'm2', category: 'answer_quality', value: -1 });
  assert.throws(() => voteArgs({ id: 'm2' }, 0));
});

test('TC-CLV-010: the score is shown overall first and then per category, in a fixed order, even for categories without votes', () => {
  const lines = scoreLines({ overall: -1, categories: { answer_quality: 1, service: -2 }, votes: 3 }, t);
  assert.deepEqual(lines.map((l) => l.key), ['overall', ...VOTE_CATEGORIES]);
  assert.deepEqual(lines.map((l) => l.value), [-1, 1, 0, 0, -2]);
  assert.equal(lines[0].label, 'vote.overall');
  assert.equal(lines[1].label, 'vote.category.answer_quality');
  assert.deepEqual(scoreLines(null, t).map((l) => l.value), [0, 0, 0, 0, 0]);
});

test('TC-CLV-011: a record needs text, and a memory record also a source; the draft is checked before it is sent', () => {
  assert.equal(itemDraftError('tasks', '  '), 'empty');
  assert.equal(itemDraftError('tasks', 'water the plants'), null);
  assert.equal(itemDraftError('memory', 'likes tea', ''), 'source');
  assert.equal(itemDraftError('memory', 'likes tea', 'chat'), null);
  assert.equal(itemDraftError('memos', 'x'.repeat(20000)), null);                       // long text is fine (FR-28: word for word)
});

test('TC-CLV-012: the trust input is a number from 0 to 1, a comma is accepted, a percentage is not guessed', () => {
  assert.equal(parseTrust('0.2'), 0.2);
  assert.equal(parseTrust('0,75'), 0.75);
  assert.equal(parseTrust('1'), 1);
  assert.equal(parseTrust('0'), 0);
  for (const bad of ['', 'abc', '1.5', '-0.1', '20', null, undefined]) assert.equal(parseTrust(bad), null, String(bad));
});

test('TC-CLV-014: the own password needs the old one, 8 characters, a repeat that matches, and must be new', () => {
  assert.equal(passwordProblem('', 'long-enough-1', 'long-enough-1'), 'empty');
  assert.equal(passwordProblem('old-secret', '', ''), 'empty');
  assert.equal(passwordProblem('old-secret', 'short', 'short'), 'short');
  assert.equal(passwordProblem('old-secret', 'long-enough-1', 'long-enough-2'), 'mismatch');
  assert.equal(passwordProblem('long-enough-1', 'long-enough-1', 'long-enough-1'), 'same');
  assert.equal(passwordProblem('old-secret', 'long-enough-1', 'long-enough-1'), null);
});

test('TC-CLV-013: the variant label names the variant, and there is none without a variant', () => {
  assert.equal(variantLabel('summer', t), 'variant.label{"name":"summer"}');
  assert.equal(variantLabel(null, t), '');
  assert.equal(variantLabel('', t), '');
});
