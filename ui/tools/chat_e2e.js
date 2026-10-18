(async () => {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const until = async (fn, ms = 8000) => { const end = Date.now() + ms; while (Date.now() < end) { if (fn()) return true; await wait(50); } return false; };
  const $ = (id) => document.getElementById(id);
  const out = {};
  const moods = [];
  new MutationObserver(() => { const x = $('mood-text').textContent; if (moods[moods.length - 1] !== x) moods.push(x); }).observe($('mood-text'), { childList: true, characterData: true, subtree: true });
  const type = (text) => { const i = $('input'); i.value = text; i.dispatchEvent(new Event('input', { bubbles: true })); };
  const rowsCount = () => document.querySelectorAll('.row').length;

  await until(() => rowsCount() > 10);
  out.initialRows = rowsCount();
  out.days = [...document.querySelectorAll('.day')].map((d) => d.textContent);
  out.olderVisible = !$('older').hidden;
  out.emptyHidden = $('empty').hidden;
  out.lastUserHasLink = !!document.querySelector('.row.user a[href^="https://example.org"]');
  out.moodAtStart = $('mood-text').textContent;

  // paging: scroll to the top loads older messages
  const list = $('messages');
  const before = rowsCount();
  list.scrollTop = 0;
  await until(() => rowsCount() > before);
  out.pagedRows = rowsCount() - before;

  // send, stream, finish
  list.scrollTop = list.scrollHeight;
  type('hello MIA');
  $('composer').requestSubmit();
  await wait(100);
  out.optimistic = !!document.querySelector('.row.user.local, .row.user:last-of-type');
  await until(() => document.querySelector('.typing') || document.querySelector('.row.assistant:last-of-type .md'));
  out.thinkingMood = $('mood-text').textContent;
  await until(() => $('stop').hidden === false, 3000);
  out.stopShown = !$('stop').hidden;
  await until(() => $('stop').hidden === true, 10000);
  const last = [...document.querySelectorAll('.row.assistant')].pop();
  out.finalHtml = last.querySelector('.msg').innerHTML.slice(0, 200);
  out.badge = last.querySelector('.badge').textContent;
  out.moodAfter = $('mood-text').textContent + ' | ' + $('mood-emoji').textContent;
  out.userState = [...document.querySelectorAll('.row.user')].pop().querySelector('[data-role=state]').textContent;

  // slash palette
  $('input').focus();
  type('/');
  await wait(100);
  out.paletteAll = $('palette').hidden ? 0 : $('palette').children.length;
  type('/li');
  await wait(100);
  out.paletteLi = $('palette').hidden ? 0 : $('palette').children.length;
  type('');
  await wait(100);
  out.paletteClosed = $('palette').hidden;

  // stop
  type('slow answer please');
  $('composer').requestSubmit();
  await until(() => $('stop').hidden === false, 5000);
  await wait(900);
  $('stop').click();
  await until(() => $('stop').hidden === true, 8000);
  await wait(300);
  const stopped = [...document.querySelectorAll('.row.assistant')].pop();
  out.stoppedState = stopped.querySelector('[data-role=state]').textContent;
  out.stoppedClass = stopped.querySelector('.msg').classList.contains('stopped');
  out.stoppedText = stopped.querySelector('.msg').textContent.slice(0, 60);

  // error
  type('trigger an error');
  $('composer').requestSubmit();
  await until(() => document.querySelector('.row.system .note'), 5000);
  await wait(300);
  out.errorNote = [...document.querySelectorAll('.row.system .note')].pop()?.textContent;
  out.moodError = $('mood-text').textContent;

  out.moodsSeen = moods;
  out.hscroll = document.documentElement.scrollWidth > innerWidth;
  out.cspErrors = window.__csp ?? 0;
  return JSON.stringify(out, null, 1);
})()
