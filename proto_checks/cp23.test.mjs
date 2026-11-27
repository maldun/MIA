// PROTOTYPE round 05 CP23 checks (node --test): the copy form offers only graphs of the same kind, and says why a copy across kinds was refused (FR-94, D-403)
import test from 'node:test';
import assert from 'node:assert/strict';
import { copyTargets, copyMessage } from '../graph_app_v2/copy-panel.js';

const graphs = [
  { id: 'research', kind: 'workflow' }, { id: 'chat.answer', kind: 'workflow' }, { id: 'old.one' },
  { id: 'ctx.main', kind: 'context' }, { id: 'ctx.side', kind: 'context' }, { id: 'odd.plan', kind: 'plan' },
];

test('FR-94: only graphs of the source graph\'s kind are offered; a graph without a kind is a workflow graph', () => {
  assert.deepEqual(copyTargets(graphs, 'research', '').map((g) => g.id), ['chat.answer', 'old.one']);
  assert.deepEqual(copyTargets(graphs, 'ctx.main', '').map((g) => g.id), ['ctx.side']);
  assert.deepEqual(copyTargets(graphs, 'odd.plan', '').map((g) => g.id), []);
});

test('FR-94: a refusal across kinds names both kinds; the other refusals give their reason; nothing was copied', () => {
  assert.equal(copyMessage(422, { error: 'kinds_differ', from_kind: 'workflow', to_kind: 'context' }, 'step', 'ctx.main'),
    'A step is copied only into a graph of the same kind: this is a workflow graph, ctx.main is a context graph. Nothing was copied.');
  assert.match(copyMessage(422, { error: 'unknown_kind', kind: 'plan' }, 'n1', 'odd.other'), /does not know the kind "plan" of odd.other.*Nothing was copied|nothing was copied/);
  assert.match(copyMessage(422, { error: 'not_editable', kind: 'context', reason: 'Editing context graphs comes with G-V4.CONTEXT.' }, 'c', 'ctx.side'), /comes with G-V4.CONTEXT\. Nothing was copied\./);
});
