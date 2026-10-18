// All texts of the interface come from dictionaries (i18n/en.json, i18n/de.json). English is the fallback.
// The page is English for now; German is prepared (?lang=de or the stored language).

const SUPPORTED = ['en', 'de'];
let fallback = {};
let current = {};

export function pickLanguage(search = '', stored = null, supported = SUPPORTED) {
  const asked = new URLSearchParams(search).get('lang');
  for (const candidate of [asked, stored]) {
    if (candidate && supported.includes(candidate)) return candidate;
  }
  return 'en';
}

export function setDictionaries(english, selected = english) {
  fallback = english || {};
  current = selected || {};
}

export async function loadLanguage(lang, fetchFn = (url) => fetch(url)) {
  const read = async (code) => {
    try {
      const response = await fetchFn(new URL(`./i18n/${code}.json`, import.meta.url));
      return response.ok ? await response.json() : {};
    } catch (error) {
      return {};
    }
  };
  const english = await read('en');
  setDictionaries(english, lang === 'en' ? english : await read(lang));
}

/** text for a key; {name} placeholders are replaced; missing keys show the key itself */
export function t(key, vars = {}) {
  const text = current[key] ?? fallback[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (match, name) => (name in vars ? String(vars[name]) : match));
}

const ATTRIBUTES = ['placeholder', 'aria-label', 'title'];

/** translates data-i18n (text) and data-i18n-<attribute> in a part of the page */
export function applyTranslations(root = document) {
  for (const element of root.querySelectorAll('[data-i18n]')) {
    element.textContent = t(element.dataset.i18n);
  }
  for (const attribute of ATTRIBUTES) {
    for (const element of root.querySelectorAll(`[data-i18n-${attribute}]`)) {
      element.setAttribute(attribute, t(element.getAttribute(`data-i18n-${attribute}`)));
    }
  }
}
