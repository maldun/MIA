// Accessibility and settings check for browser_check.py --eval (needs ui/tools/chat_stub_server.py running):
//   python ui/tools/browser_check.py "http://127.0.0.1:8685/?character=0" shot.png --eval "$(cat ui/tools/chat_a11y.js)"
// Add --mobile --size 320x640 to measure the touch targets on a small phone.
(async () => {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const $ = (id) => document.getElementById(id);
  const out = {};
  const key = (k, extra = {}, target = document.body) => target.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true, ...extra }));
  await wait(1500);

  // semantics
  out.logLive = $('messages').getAttribute('aria-live');
  out.logRole = $('messages').getAttribute('role');
  out.announceLive = $('announce').getAttribute('aria-live');

  // shortcuts
  $('input').blur();
  key('/');
  out.slashFocusesComposer = document.activeElement === $('input');
  key('c', { altKey: true });
  await wait(500);
  out.altCCollapses = $('panel').dataset.collapsed;
  key('c', { altKey: true });
  await wait(500);
  out.altCReopens = $('panel').dataset.collapsed;
  key('m', { altKey: true });
  out.altMMenu = !$('menu').hidden;
  key('Escape');
  out.escMenu = $('menu').hidden;

  // settings
  $('menu-button').click();
  $('settings-button').click();
  await wait(200);
  out.dialogOpen = $('settings').open;
  $('set-compact').click();
  $('set-times').click();
  $('set-emotions').click();
  $('set-mood').click();
  await wait(200);
  const root = document.documentElement.dataset;
  out.attrs = { compact: root.compact, times: root.times, emotions: root.emotions };
  out.moodHidden = $('mood').hidden;
  out.timesHidden = getComputedStyle(document.querySelector('.msg-foot time')).display;
  out.stored = localStorage.getItem('mia.settings');
  $('settings-reset').click();
  await wait(200);
  out.afterReset = { compact: root.compact, times: root.times, mood: !$('mood').hidden, stored: localStorage.getItem('mia.settings') };
  $('settings-close').click();

  // announcement of a finished answer, list not live
  $('input').value = 'hello';
  $('input').dispatchEvent(new Event('input', { bubbles: true }));
  $('composer').requestSubmit();
  const start = Date.now();
  while (Date.now() - start < 9000 && !$('announce').textContent) await wait(100);
  out.announced = $('announce').textContent.slice(0, 60);
  out.busyAfter = $('messages').getAttribute('aria-busy');

  // touch targets and overflow
  const small = [];
  for (const el of document.querySelectorAll('button, a.menu-item, select, input[type=checkbox], input[type=range]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || el.closest('[hidden]') || el.closest('dialog:not([open])')) continue;
    if (r.width < 44 || r.height < 44) small.push(`${el.id || el.className || el.tagName}:${Math.round(r.width)}x${Math.round(r.height)}`);
  }
  out.smallTargets = small;
  out.hscroll = document.documentElement.scrollWidth > innerWidth;
  out.coarse = matchMedia('(pointer: coarse)').matches;
  return JSON.stringify(out, null, 1);
})()
