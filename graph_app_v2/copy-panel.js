// PROTOTYPE CP10 (G-V4.EDIT, FR-94): copy the selected step into another graph. Built only with createElement and textContent.
import { filterGraphs, entryLabel } from './list-filter.js';

const el = (doc, tag, text) => { const e = doc.createElement(tag); if (text !== undefined) e.textContent = text; return e; };

/** the graphs a step can be copied into: every other stored graph of the same kind (round 05 CP23, FR-94, D-403), narrowed by what was typed */
export function copyTargets(graphs, sourceId, text) {
  const kind = (graphs ?? []).find((g) => g.id === sourceId)?.kind ?? 'workflow';
  return filterGraphs((graphs ?? []).filter((g) => g.id !== sourceId && (g.kind ?? 'workflow') === kind), text);
}

/** what the owner is told after the copy was tried; `status` is the HTTP status, `body` the answer */
export function copyMessage(status, body, step, target) {
  if (status === 200) return `Copied "${step}" into ${target} as "${body.step}": ${target} is now version ${body.version}.${body.synced === false ? ` The copy could not be updated (${body.sync_problem}).` : ''}`;
  if (status === 409 && body?.error === 'name_taken') return `${target} already has a step named "${body.name}": choose another name for the copy.`;
  if (status === 422 && body?.rules) return `The copy would break a rule in ${target} and was not made: ${body.rules.map((r) => `${r.rule} (${r.parts.join(', ')})`).join('; ')}`;
  if (status === 422 && body?.error === 'same_graph') return 'Choose another graph: a step is copied into a different graph.';
  if (status === 422 && body?.error === 'kinds_differ') return `A step is copied only into a graph of the same kind: this is a ${body.from_kind} graph, ${target} is a ${body.to_kind} graph. Nothing was copied.`;
  if (status === 422 && body?.error === 'unknown_kind') return `The program does not know the kind "${body.kind}" of ${target}: nothing was copied.`;
  if (status === 422 && body?.error === 'not_editable') return `${body.reason} Nothing was copied.`;
  if (status === 503) return 'The live store cannot be reached: nothing was copied.';
  if (status === 403) return 'Only the owner can copy a step into a graph.';
  return `The step was not copied (${status} ${body?.error ?? ''}).`;
}

/** the copy form under a selected step: a search over the other graphs, a name for the copy, the button; `onCopy({target, name})` does the request */
export function renderCopyPanel(doc, container, step, graphs, sourceId, { onCopy }) {
  let chosen = '';
  const box = el(doc, 'section');
  box.append(el(doc, 'h3', `Copy "${step.id}" into another graph`));
  const shown = el(doc, 'p');
  const search = el(doc, 'input'); search.setAttribute('type', 'search'); search.setAttribute('aria-label', 'search the graph to copy into'); search.setAttribute('placeholder', 'search the other graph by name');
  const list = el(doc, 'ul'); list.setAttribute('role', 'listbox'); list.setAttribute('aria-label', 'graphs to copy into');
  const name = el(doc, 'input'); name.value = step.id; name.setAttribute('aria-label', 'name of the copy');
  const button = el(doc, 'button', 'Copy the step'); button.type = 'button';
  const render = () => {
    shown.textContent = chosen ? `Into: ${chosen}` : 'Into: (no graph chosen yet)';
    button.disabled = !chosen;
    list.replaceChildren(...copyTargets(graphs, sourceId, search.value).map((g) => {
      const li = el(doc, 'li', entryLabel(g));
      li.setAttribute('role', 'option'); li.setAttribute('aria-selected', String(g.id === chosen)); li.tabIndex = 0;
      const choose = () => { chosen = g.id; render(); };
      li.addEventListener('click', choose);
      li.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault?.(); choose(); } });
      return li;
    }));
  };
  search.addEventListener('input', render);
  button.addEventListener('click', () => { if (chosen) onCopy({ target: chosen, name: name.value.trim() }); });
  render();
  const label = el(doc, 'label'); label.append(el(doc, 'span', 'name of the copy'), name);
  box.append(shown, search, list, label, button);
  container.append(box);
  return { search, list, name, button, get chosen() { return chosen; } };
}
