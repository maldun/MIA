// PROTOTYPE CP8 (G-V4.EDIT): the editing panel, built only with createElement and textContent; inputs get their value through .value (never markup).
import { formFor, applyForm, KINDS } from './edit-model.js';

const el = (doc, tag, text) => { const e = doc.createElement(tag); if (text !== undefined) e.textContent = text; return e; };

function labelled(doc, labelText, input, error) {
  const label = el(doc, 'label'); label.append(el(doc, 'span', labelText), input);
  const wrap = el(doc, 'div'); wrap.append(label);
  if (error) { const e = el(doc, 'p', error); e.setAttribute('role', 'alert'); e.className = 'field-error'; wrap.append(e); }
  return wrap;
}

/** the form of one step: its known fields, the rest as JSON text, and the buttons; `onApply(data)` gets the new content, `onRemove()` removes the step */
/** the tools as a list: the entries of the toolbox with their trust and lifecycle (controllers for a loop-controlling step, the others for a processing step);
 *  a tool that is stored but not in the toolbox stays selectable at the top, marked */
function toolSelect(doc, tools, current, controller) {
  const select = el(doc, 'select');
  select.setAttribute('aria-label', 'tool (toolbox entry)');
  const list = (tools ?? []).filter((t) => t.controller === controller);
  const known = new Set(list.map((t) => t.id));
  const options = [];
  if (!current) options.push({ id: '', label: '(choose a tool)' });
  else if (!known.has(current)) options.push({ id: current, label: `${current}  (not in the toolbox)` });
  options.push(...list.map((t) => ({ id: t.id, label: `${t.id}  (${t.trust}, ${t.lifecycle})` })));
  for (const o of options) { const op = el(doc, 'option', o.label); op.value = o.id; select.append(op); }
  select.value = current ?? '';
  return select;
}

export function renderStepEditor(doc, container, step, { onApply, onRemove, errors = {}, tools = null }) {
  const form = formFor(step);
  const inputs = {};
  const box = el(doc, 'div');
  box.append(el(doc, 'h3', `Edit step: ${step.id}`));
  const kind = el(doc, 'p', `kind: ${KINDS[(step.data ?? {}).type] ?? 'unknown'} (the kind cannot be changed; remove the step and add another)`);
  box.append(kind);
  for (const f of form.fields) {
    const input = f.name === 'toolbox_id' && tools ? toolSelect(doc, tools, String(f.value), (step.data ?? {}).type === 'master') : el(doc, 'input');
    if (!(f.name === 'toolbox_id' && tools)) { input.value = String(f.value); input.setAttribute('aria-label', f.label); }
    if (f.kind === 'number') input.setAttribute('inputmode', 'decimal');
    inputs[f.name] = input;
    box.append(labelled(doc, f.label, input, errors[f.name]));
  }
  const other = el(doc, 'textarea'); other.value = form.other; other.setAttribute('aria-label', 'other stored fields as JSON text'); other.rows = 4;
  box.append(labelled(doc, 'other fields (JSON text)', other, errors.other));
  const apply = el(doc, 'button', 'Apply to the working copy'); apply.type = 'button';
  apply.addEventListener('click', () => {
    const values = Object.fromEntries(Object.entries(inputs).map(([k, v]) => [k, v.value]));
    onApply(applyForm(step, values, other.value));
  });
  const remove = el(doc, 'button', 'Remove this step'); remove.type = 'button';
  remove.addEventListener('click', () => onRemove());
  box.append(apply, remove);
  container.replaceChildren(box);
  return { inputs, other, apply, remove };
}

/** the form of one connection: role and name, and the button to remove it */
export function renderConnectionEditor(doc, container, link, { onApply, onRemove }) {
  const box = el(doc, 'div');
  box.append(el(doc, 'h3', `Edit connection: ${link.id}`), el(doc, 'p', `${link.from} → ${link.to}`));
  const role = el(doc, 'input'); role.value = (link.data ?? {}).role ?? ''; role.setAttribute('aria-label', 'role');
  const as = el(doc, 'input'); as.value = (link.data ?? {}).as ?? ''; as.setAttribute('aria-label', 'name');
  box.append(labelled(doc, 'role (settings, order, code or empty)', role), labelled(doc, 'name', as));
  const apply = el(doc, 'button', 'Apply to the working copy'); apply.type = 'button';
  apply.addEventListener('click', () => onApply({ role: role.value.trim(), as: as.value.trim() }));
  const remove = el(doc, 'button', 'Remove this connection'); remove.type = 'button';
  remove.addEventListener('click', () => onRemove());
  box.append(apply, remove);
  container.replaceChildren(box);
  return { role, as, apply, remove };
}
