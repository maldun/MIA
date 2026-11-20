// PROTOTYPE CP6 (G-V4.VIEW): the kind of a step and its marks at a glance (FR-50), and the known values of a step as read-only fields (FR-51).
// Pure: strings in, strings out, so it is tested without a browser and nothing here can become markup.

/** the shape of each kind: the kinds differ by shape and by words, never by colour alone */
export const SHAPES = { data: 'ellipse', process: 'box', master: 'hexagon', missing: 'box' };
export const KIND_NAMES = { data: 'data', transform: 'processing', master: 'loop-controlling', missing: 'missing step' };

/** the vis group of a stored step type */
export const groupOf = (type) => (type === 'data' ? 'data' : type === 'master' ? 'master' : type === 'missing' ? 'missing' : 'process');

/** the marks of a processing or loop-controlling step: trust, changed since trusted, lifecycle, code. Data steps have none. */
export function marksOf(info) {
  if (!info || (info.kind !== 'transform' && info.kind !== 'master')) return [];
  const marks = [info.trust === 'trusted' ? 'trusted' : 'UNTRUSTED'];
  if (info.changed_since_trusted) marks.push('changed since trusted');
  if (info.lifecycle) marks.push(info.lifecycle);
  if (info.code) marks.push('code');
  return marks;
}

/** the label drawn on the canvas: the id, and the marks on a second line (plain text; vis does not read markup here) */
export const labelOf = (id, info) => { const m = marksOf(info); return m.length ? `${id}\n${m.join(' · ')}` : String(id); };

const show = (v) => (typeof v === 'string' ? v : JSON.stringify(v));

/** the known values of a step as [{label, value}], all text, read-only; whatever else is stored is in the full text */
export function fieldsOf(step, info) {
  if (!step) return [];
  const data = step.data ?? {};
  const rows = [['step', step.id], ['kind', KIND_NAMES[data.type] ?? 'unknown']];
  if (data.toolbox_id !== undefined) rows.push(['tool', data.toolbox_id]);
  if (data.value !== undefined) rows.push(['value', show(data.value)]);
  if (data.parameters && Object.keys(data.parameters).length) rows.push(['parameters', show(data.parameters)]);
  if (data.stop) rows.push(['stops at', show(data.stop)]);
  if (info && (info.kind === 'transform' || info.kind === 'master')) {
    rows.push(['trust', info.trust === 'trusted' ? 'trusted' : 'untrusted']);
    if (info.reason) rows.push(['why untrusted', info.reason]);
    if (info.lifecycle) rows.push(['lifecycle', info.lifecycle]);
    if (info.changed_since_trusted) rows.push(['changed', 'since it was trusted']);
    if (info.code) rows.push(['code', 'this step holds code']);
  }
  return rows.map(([label, value]) => ({ label, value: String(value) }));
}

/** the fields of a connection */
export function connectionFields(link) {
  if (!link) return [];
  const rows = [['connection', link.id], ['from', link.from], ['to', link.to]];
  const data = link.data ?? {};
  if (data.role) rows.push(['role', data.role]);
  if (data.as) rows.push(['name', data.as]);
  return rows.map(([label, value]) => ({ label, value: String(value) }));
}

/** the complete stored content as plain text */
export const fullText = (item) => JSON.stringify(item, null, 2);

/** vis-network draws the label of a hexagon outside the shape (or not at all), so the loop-controlling step is drawn here: a hexagon that fits its text,
 *  the step name and its marks inside. `untrusted` is the set of step IDs drawn with a dashed border, like the other untrusted steps. */
export function makeHexagonRenderer(colors, untrusted = new Set()) {
  return ({ ctx, id, x, y, state, label }) => {
    const lines = String(label ?? '').split('\n');
    const font = '14px system-ui, sans-serif';
    ctx.font = font;
    const lineHeight = 17, padX = 22, padY = 10;
    const width = Math.max(...lines.map((l) => ctx.measureText(l).width)) + 2 * padX;
    const height = lines.length * lineHeight + 2 * padY;
    const tip = Math.min(18, height / 2);
    return {
      drawNode() {
        ctx.save();
        ctx.beginPath();
        const pts = [[x - width / 2, y], [x - width / 2 + tip, y - height / 2], [x + width / 2 - tip, y - height / 2], [x + width / 2, y], [x + width / 2 - tip, y + height / 2], [x - width / 2 + tip, y + height / 2]];
        pts.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
        ctx.closePath();
        ctx.fillStyle = colors.fill;
        ctx.fill();
        ctx.lineWidth = state?.selected ? 3 : 1;
        ctx.strokeStyle = colors.line;
        if (untrusted.has(id)) ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = colors.text;
        ctx.font = font;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        lines.forEach((line, i) => ctx.fillText(line, x, y - ((lines.length - 1) * lineHeight) / 2 + i * lineHeight));
        ctx.restore();
      },
      drawExternalLabel() {},
      nodeDimensions: { width, height },
    };
  };
}
