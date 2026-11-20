// PROTOTYPE CP8 (G-V4.EDIT): the editing panel, built only with createElement and textContent; inputs get their value through .value (never markup).
import { formFor, applyForm, KINDS, filterTools, toolLabel } from './edit-model.js';

const el = (doc, tag, text) => { const e = doc.createElement(tag); if (text !== undefined) e.textContent = text; return e; };

function labelled(doc, labelText, input, error) {
  const label = el(doc, 'label'); label.append(el(doc, 'span', labelText), input);
  const wrap = el(doc, 'div'); wrap.append(label);
  if (error) { const e = el(doc, 'p', error); e.setAttribute('role', 'alert'); e.className = 'field-error'; wrap.append(e); }
  return wrap;
}

/** the form of one step: its known fields, the rest as JSON text, and the buttons; `onApply(data)` gets the new content, `onRemove()` removes the step */
/** the tool of a step: a search box over the entries of the toolbox with their trust and lifecycle (controllers for a loop-controlling step, the others for a
 *  processing step), as a list like the list of graphs; a stored tool that is not in the toolbox stays choosable, marked. `value` is the tool chosen. */
function toolPicker(doc, tools, current, controller) {
  let chosen = current ?? '';
  const wrap = el(doc, 'div');
  const shown = el(doc, 'p');
  const search = el(doc, 'input'); search.setAttribute('type', 'search'); search.setAttribute('aria-label', 'search tools'); search.setAttribute('placeholder', 'search tools by name');
  const list = el(doc, 'ul'); list.setAttribute('role', 'listbox'); list.setAttribute('aria-label', 'tools of the toolbox');
  const label = (id) => { const t = (tools ?? []).find((x) => x.id === id); return id ? (t ? toolLabel(t) : `${id}  (not in the toolbox)`) : '(none chosen yet)'; };
  const render = () => {
    shown.textContent = `Tool: ${label(chosen)}`;
    const matches = filterTools(tools, search.value, controller);
    const words = String(search.value ?? '').toLowerCase().split(/\s+/).filter(Boolean);
    const stored = current && !(tools ?? []).some((t) => t.id === current) && words.every((w) => current.toLowerCase().includes(w));   // a stored tool outside the toolbox is listed while it matches
    const rows = [...(stored ? [{ id: current, text: `${current}  (not in the toolbox)` }] : []), ...matches.map((t) => ({ id: t.id, text: toolLabel(t) }))];
    list.replaceChildren(...rows.map((r) => {
      const li = el(doc, 'li', r.text);
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', String(r.id === chosen));
      li.tabIndex = 0;
      const choose = () => { chosen = r.id; render(); };
      li.addEventListener('click', choose);
      li.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault?.(); choose(); } });
      return li;
    }));
  };
  search.addEventListener('input', render);
  render();
  wrap.append(shown, search, list);
  return { element: wrap, get value() { return chosen; }, set value(v) { chosen = v; render(); }, list, search };
}

export function renderStepEditor(doc, container, step, { onApply, onRemove, errors = {}, tools = null }) {
  const form = formFor(step);
  const inputs = {};
  const box = el(doc, 'div');
  box.append(el(doc, 'h3', `Edit step: ${step.id}`));
  const kind = el(doc, 'p', `kind: ${KINDS[(step.data ?? {}).type] ?? 'unknown'} (the kind cannot be changed; remove the step and add another)`);
  box.append(kind);
  for (const f of form.fields) {
    if (f.name === 'toolbox_id' && tools) {
      const picker = toolPicker(doc, tools, String(f.value), (step.data ?? {}).type === 'master');
      inputs[f.name] = picker;
      const wrap = el(doc, 'div'); wrap.append(el(doc, 'span', f.label), picker.element);
      if (errors[f.name]) { const e = el(doc, 'p', errors[f.name]); e.setAttribute('role', 'alert'); e.className = 'field-error'; wrap.append(e); }
      box.append(wrap);
      continue;
    }
    const input = el(doc, 'input'); input.value = String(f.value); input.setAttribute('aria-label', f.label);
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
