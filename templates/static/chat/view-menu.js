// Menu entries for the character: camera view (body, bust, face) and the background picture of the backgrounds folder.
// Both talk to the character through the host bridge ({"type": "view"} / {"type": "background"}) and are remembered per device.

export const VIEWS = ['body', 'bust', 'face'];

export async function loadBackgrounds(origin = location.origin) {
  try {
    const response = await fetch(new URL('/character-backgrounds.json', origin));
    return response.ok ? await response.json() : { files: [], default: '' };
  } catch (error) {
    return { files: [], default: '' };
  }
}

export function initViewMenu({ buttons, group, select, character, storage, t }) {
  let view = VIEWS.includes(storage.get('mia.view')) ? storage.get('mia.view') : 'body';
  let backgrounds = { files: [], default: '' };

  function markView() {
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.view === view));
  }

  for (const button of buttons) {
    button.addEventListener('click', () => {
      view = button.dataset.view;
      storage.set('mia.view', view);
      character.setView(view);
      markView();
    });
  }

  select.addEventListener('change', () => {
    storage.set('mia.background', select.value);
    character.setBackground(select.value);
  });

  async function fillBackgrounds() {
    backgrounds = await loadBackgrounds();
    if (!backgrounds.files.length) return;
    select.textContent = '';
    const none = document.createElement('option');
    none.value = '';
    none.textContent = t('background.none');
    select.append(none);
    for (const file of backgrounds.files) {
      const option = document.createElement('option');
      option.value = file;
      option.textContent = file;
      select.append(option);
    }
    select.value = storage.get('mia.background') ?? backgrounds.default ?? '';
    group.hidden = false;
  }

  markView();
  fillBackgrounds();

  return {
    /** the character just loaded: it gets the choices of this device */
    apply() {
      if (storage.get('mia.view')) character.setView(view);
      if (storage.get('mia.background') !== null) character.setBackground(storage.get('mia.background'));
    },
  };
}
