// PROTOTYPE CP8 (G-V4.EDIT): the editing panel, built only with createElement and textContent; inputs get their value through .value (never markup).
// Round 05 CP21: every control comes from the profile of the graph's kind (edit-model.js, GET /api/v2/kinds); no kind of step is named here.
import { formFor, applyForm, typeName, filterTools, toolLabel } from './edit-model.js';

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
function toolPicker(doc, tools, current, filter, keepUnknown = true) {
  let chosen = current ?? '';
  const wrap = el(doc, 'div');
  const shown = el(doc, 'p');
  const search = el(doc, 'input'); search.setAttribute('type', 'search'); search.setAttribute('aria-label', 'search tools'); search.setAttribute('placeholder', 'search tools by name');
  const list = el(doc, 'ul'); list.setAttribute('role', 'listbox'); list.setAttribute('aria-label', 'tools of the toolbox');
  const label = (id) => { const t = (tools ?? []).find((x) => x.id === id); return id ? (t ? toolLabel(t) : `${id}  (not in the toolbox)`) : '(none chosen yet)'; };
  const render = () => {
    shown.textContent = `Tool: ${label(chosen)}`;
    const matches = filterTools(tools, search.value, filter);
    const words = String(search.value ?? '').toLowerCase().split(/\s+/).filter(Boolean);
    const stored = keepUnknown && current && !(tools ?? []).some((t) => t.id === current) && words.every((w) => current.toLowerCase().includes(w));   // a stored tool outside the toolbox is listed while it matches
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

/** a choice from a fixed list of options (the empty option reads "(none)") */
function optionPicker(doc, field, value) {
  const select = el(doc, 'select'); select.setAttribute('aria-label', field.label);
  for (const o of field.options) { const opt = el(doc, 'option', o || '(none)'); opt.value = o; select.append(opt); }
  select.value = value;
  return select;
}

export function renderStepEditor(doc, container, step, { onApply, onRemove, errors = {}, tools = null, profile = null }) {
  const form = formFor(step, profile);
  const inputs = {};
  const box = el(doc, 'div');
  box.append(el(doc, 'h3', `Edit step: ${step.id}`));
  const kind = el(doc, 'p', `kind: ${typeName(profile, (step.data ?? {}).type)} (the kind cannot be changed; remove the step and add another)`);
  box.append(kind);
  for (const f of form.fields) {
    if (f.input === 'choice' && f.list === 'toolbox' && tools) {
      const picker = toolPicker(doc, tools, String(f.value), f.filter ?? {}, f.keep_unknown !== false);
      inputs[f.name] = picker;
      const wrap = el(doc, 'div'); wrap.append(el(doc, 'span', f.label), picker.element);
      if (errors[f.name]) { const e = el(doc, 'p', errors[f.name]); e.setAttribute('role', 'alert'); e.className = 'field-error'; wrap.append(e); }
      box.append(wrap);
      continue;
    }
    if (f.input === 'choice' && f.options) {
      const select = optionPicker(doc, f, String(f.value));
      inputs[f.name] = select;
      box.append(labelled(doc, f.label, select, errors[f.name]));
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
    onApply(applyForm(step, values, other.value, profile));
  });
  const remove = el(doc, 'button', 'Remove this step'); remove.type = 'button';
  remove.addEventListener('click', () => onRemove());
  box.append(apply, remove);
  container.replaceChildren(box);
  return { inputs, other, apply, remove };
}

/** the form of one connection: the connection fields of the profile, and the button to remove it */
export function renderConnectionEditor(doc, container, link, { onApply, onRemove, profile = null }) {
  const box = el(doc, 'div');
  box.append(el(doc, 'h3', `Edit connection: ${link.id}`), el(doc, 'p', `${link.from} → ${link.to}`));
  const inputs = {};
  for (const f of profile?.connection_fields ?? []) {
    const value = String((link.data ?? {})[f.name] ?? '');
    let input;
    if (f.input === 'choice' && f.options) input = optionPicker(doc, f, value);
    else { input = el(doc, 'input'); input.value = value; input.setAttribute('aria-label', f.label); }
    inputs[f.name] = input;
    box.append(labelled(doc, f.label, input));
  }
  const apply = el(doc, 'button', 'Apply to the working copy'); apply.type = 'button';
  apply.addEventListener('click', () => onApply(Object.fromEntries(Object.entries(inputs).map(([k, v]) => [k, String(v.value).trim()]))));
  const remove = el(doc, 'button', 'Remove this connection'); remove.type = 'button';
  remove.addEventListener('click', () => onRemove());
  box.append(apply, remove);
  container.replaceChildren(box);
  return { inputs, role: inputs.role, as: inputs.as, apply, remove };
}
