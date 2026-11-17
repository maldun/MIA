// The status line of a skill run in the chat: always the last element, replaced in place, removed when cleared (A-158, REQ-CLV-053, 054).
// TC-CLV-053 (the model part; the page wiring is checked in the browser with the stub server).  node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { runLineState, withRunLine } from '../../templates/static/chat/chat-model.js';

const msg = (id, text) => ({ id, role: 'assistant', text });

test('TC-CLV-053: the status line stays the last element, is replaced in place and is removed when it is cleared', () => {
  // Given: two messages and the event of a status line `collect` of run r1
  const messages = [msg(1, 'Question'), msg(2, 'Answer')];
  let line = runLineState(null, { run: 'r1', text: 'collect' });
  // When: the chat shows the messages with the line, a third message arrives, the line changes to `rank`
  const first = withRunLine(messages, line);
  const more = [...messages, msg(3, 'Another')];
  line = runLineState(line, { run: 'r1', text: 'rank' });
  const second = withRunLine(more, line);
  // Then: the line is the last element both times, shows `rank` in place (one line) and holds the link of the run
  assert.equal(first.at(-1).text, 'collect');
  assert.equal(second.at(-1).text, 'rank');
  assert.equal(second.filter((item) => item.kind === 'run_line').length, 1);
  assert.equal(second.at(-1).href, '#run=r1');
  assert.deepEqual(second.slice(0, 3), more);
  // And: when the line is cleared and the end message arrives, no line is left and the end message is last
  line = runLineState(line, { run: 'r1', text: null });
  const ended = withRunLine([...more, msg(4, 'Done')], line);
  assert.equal(line, null);
  assert.deepEqual(ended.map((item) => item.id), [1, 2, 3, 4]);
});

test('TC-CLV-053: the clearing of another run leaves the line of the run that is shown', () => {
  // Given: a line of run r1
  const line = runLineState(null, { run: 'r1', text: 'collect' });
  // When: the clearing of run r2 comes in
  const after = runLineState(line, { run: 'r2', text: null });
  // Then: the line of r1 is still there
  assert.deepEqual(after, { run: 'r1', text: 'collect' });
});
