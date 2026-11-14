// The two height shares of the Skill run view (REQ-CLV-045, REQ-CLV-046): the strip (12 to 40 % of the window height, default 16) and the Full run part (20 to 60 %, default 34).
// They are a setting of this browser: kept in the storage of the device, applied at every load, and the defaults are used when the browser refuses to store. A value outside the range is refused.
export const SHARES = {
  strip: { key: 'mia.srv.strip', min: 12, max: 40, fallback: 16, variable: '--srv-strip-share' },
  full: { key: 'mia.srv.full', min: 20, max: 60, fallback: 34, variable: '--srv-full-share' },
};

export function validShare(name, value) {
  const { min, max } = SHARES[name];
  const number = typeof value === 'string' && value.trim() === '' ? NaN : Number(value);
  return Number.isInteger(number) && number >= min && number <= max ? number : null;
}

export function initShares({ storage, inputs, root = document.documentElement }) {
  const current = {};
  function apply(name, value) {
    current[name] = value;
    root.style.setProperty(SHARES[name].variable, String(value));
    inputs[name].value = String(value);
  }
  for (const [name, spec] of Object.entries(SHARES)) {
    apply(name, validShare(name, storage.get(spec.key)) ?? spec.fallback);
    inputs[name].min = String(spec.min);
    inputs[name].max = String(spec.max);
    inputs[name].addEventListener('input', () => {      // a valid value takes effect at once, a half-typed one waits for the change
      const value = validShare(name, inputs[name].value);
      if (value !== null && value !== current[name]) {
        apply(name, value);
        storage.set(spec.key, value);
      }
    });
    inputs[name].addEventListener('change', () => {      // a refused value goes back to the one in use
      const value = validShare(name, inputs[name].value);
      if (value === null) inputs[name].value = String(current[name]);
    });
  }
  return { get: () => ({ ...current }) };
}
