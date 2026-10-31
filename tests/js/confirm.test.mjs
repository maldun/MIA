// The confirmation of the commands that switch the model (REQ-RUN-002, D-128): node --test "tests/js/*.test.mjs"
import test from 'node:test';
import assert from 'node:assert/strict';
import { sendConfirmed } from '../../templates/static/chat/chat-model.js';

const COMMANDS = [
  { command: '/light!', confirm: true, description: 'switch to the light model' },
  { command: '/full!', confirm: true, description: 'switch to the full model' },
  { command: '/lookup', confirm: false, description: 'look something up' },
];

function recorder(answer) {
  const asked = [];
  const sent = [];
  return {
    asked,
    sent,
    confirm: async (command) => { asked.push(command.command); return answer; },
    send: (text) => { sent.push(text); },
  };
}

test('TC-RUN-002: /light! is not sent when the user says no', async () => {
  const r = recorder(false);
  const result = await sendConfirmed('/light!', COMMANDS, r.confirm, r.send);
  assert.equal(result, false);
  assert.deepEqual(r.asked, ['/light!']);
  assert.deepEqual(r.sent, []);
});

test('TC-RUN-002: /full! is not sent when the user says no', async () => {
  const r = recorder(false);
  const result = await sendConfirmed('/full!', COMMANDS, r.confirm, r.send);
  assert.equal(result, false);
  assert.deepEqual(r.asked, ['/full!']);
  assert.deepEqual(r.sent, []);
});

test('TC-RUN-002: /light! is sent after a yes', async () => {
  const r = recorder(true);
  const result = await sendConfirmed('/light!', COMMANDS, r.confirm, r.send);
  assert.equal(result, true);
  assert.deepEqual(r.asked, ['/light!']);
  assert.deepEqual(r.sent, ['/light!']);
});

test('TC-RUN-002: the command is recognised in any case and sent as typed', async () => {
  const r = recorder(true);
  await sendConfirmed('/LIGHT!', COMMANDS, r.confirm, r.send);
  assert.deepEqual(r.asked, ['/light!']);
  assert.deepEqual(r.sent, ['/LIGHT!']);
});

test('TC-RUN-002: a command without confirmation and a plain message are sent without asking', async () => {
  const r = recorder(false);
  assert.equal(await sendConfirmed('/lookup', COMMANDS, r.confirm, r.send), true);
  assert.equal(await sendConfirmed('Hello MIA', COMMANDS, r.confirm, r.send), true);
  assert.deepEqual(r.asked, []);
  assert.deepEqual(r.sent, ['/lookup', 'Hello MIA']);
});
