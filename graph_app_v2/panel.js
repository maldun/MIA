// PROTOTYPE CP6 (G-V4.VIEW): the left panel and the step list, built only with createElement and textContent (FR-54: nothing stored is ever markup).
import { fieldsOf, connectionFields, fullText, labelOf } from './step-marks.js';

/** shows the known fields of a step or connection as labelled read-only values, and the full stored text below; nothing selected clears it */
export function renderPanel(doc, container, item, info, isConnection = false) {
  if (!item) { const p = doc.createElement('p'); p.textContent = 'Click a step or a connection.'; container.replaceChildren(p); return; }
  const list = doc.createElement('dl');
  for (const { label, value } of (isConnection ? connectionFields(item) : fieldsOf(item, info))) {
    const dt = doc.createElement('dt'); dt.textContent = label;
    const dd = doc.createElement('dd'); dd.textContent = value;
    list.append(dt, dd);
  }
  const details = doc.createElement('details');
  const summary = doc.createElement('summary'); summary.textContent = 'Full stored text';
  const pre = doc.createElement('pre'); pre.textContent = fullText(item);
  details.append(summary, pre);
  container.replaceChildren(list, details);
}

/** the steps of a graph as a list that a keyboard reaches (Tab) and selects (Enter or Space): the other way to a step besides the picture (NFR-14) */
export function renderStepList(doc, container, graph, infos, onPick) {
  const items = graph.nodes.map((step) => {
    const li = doc.createElement('li');
    li.textContent = labelOf(step.id, infos[step.id]).replace('\n', '  ');
    li.setAttribute('role', 'option');
    li.tabIndex = 0;
    const pick = () => onPick(step.id);
    li.addEventListener('click', pick);
    li.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault?.(); pick(); } });
    return li;
  });
  container.replaceChildren(...items);
  return items;
}
