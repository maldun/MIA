// Click-through of the views of IF-101 v1 (N-1.1): actions under an answer, regenerate, variant label, workspace (tasks, memory, sources, persona, score), account.
// Needs the mock server (ANSWER_DELAY=1 EVENT_GAP=0.05 python ui/tools/chat_mock_server.py) and a headless browser that is logged in as anna / pw-anna
// (the form of the login dialog). Returns {problems: []} when everything is as expected. It changes the password of anna to long-enough-1 at the end.
(async () => {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const until = async (fn, ms = 8000) => { const end = Date.now() + ms; while (Date.now() < end) { if (fn()) return true; await wait(50); } return false; };
  const $ = (id) => document.getElementById(id);
  const out = { problems: [] };
  const check = (cond, what) => { if (!cond) out.problems.push(what); return cond; };
  const rows = () => [...document.querySelectorAll('#messages .row')];
  const answers = () => rows().filter((r) => r.classList.contains('assistant'));
  const visible = (el) => el && !el.hidden;
  const toasts = () => document.querySelector('.toast, [role=status].toast')?.textContent;

  // --- a message and its answer: the actions under the answer ------------------------------------------------
  const input = $('input');
  input.value = 'hello views'; input.dispatchEvent(new Event('input', { bubbles: true })); $('send').click();
  check(await until(() => answers().length >= 1 && answers().at(-1).querySelector('[data-role=bubble]')?.textContent.includes('How are you'), 12000), 'the first answer arrives');
  await wait(600);
  const first = answers().at(-1);
  const btn = (row, action) => row.querySelector(`[data-action=${action}]`);
  out.firstActions = ['speak', 'up', 'down', 'how', 'regenerate'].map((a) => `${a}:${visible(btn(first, a))}`);
  check(['speak', 'up', 'down', 'how', 'regenerate'].every((a) => visible(btn(first, a))), 'all five actions are shown on the last answer');

  btn(first, 'up').click(); await wait(500);
  check(btn(first, 'up').getAttribute('aria-pressed') === 'true' && btn(first, 'down').getAttribute('aria-pressed') === 'false', 'the plus is marked after a vote');
  btn(first, 'how').click(); await wait(500);
  const lis = first.querySelectorAll('.account li');
  out.account = [...lis].map((l) => l.textContent);
  check(lis.length === 2, 'the account of the answer lists two steps');
  btn(first, 'how').click(); await wait(100);
  check(first.querySelector('.account').hidden === true, 'a second click hides the account');
  btn(first, 'speak').click(); await wait(300);

  // --- regenerate: a new answer, the button moves to it ---------------------------------------------------------
  btn(first, 'regenerate').click();
  check(await until(() => answers().length >= 2 && answers().at(-1).querySelector('[data-role=bubble]')?.textContent.length > 5, 12000), 'a new answer arrives after regenerate');
  await wait(800);
  const second = answers().at(-1);
  check(second !== first, 'the regenerated answer is a new message');
  check(visible(btn(second, 'regenerate')) && !visible(btn(first, 'regenerate')), 'regenerate moved to the new last answer');
  out.answers = answers().map((r) => r.querySelector('[data-role=bubble]')?.textContent.trim().slice(0, 30));

  // --- the variant label comes with every third answer (the mock) ---------------------------------------------
  for (let n = 0; n < 1; n += 1) {
    input.value = 'third'; input.dispatchEvent(new Event('input', { bubbles: true })); $('send').click();
    await until(() => answers().length >= 3, 12000); await wait(1500);
  }
  out.variantLabel = visible($('variant')) ? $('variant').textContent : null;
  check(out.variantLabel === 'Outfit: summer', 'the variant label shows the outfit of the third answer');

  // --- workspace ---------------------------------------------------------------------------------------------------
  $('menu-button').click(); await wait(200);
  $('workspace-button').click(); await wait(800);
  check($('workspace').open, 'the workspace opens');
  const tabs = [...$('workspace-tabs').querySelectorAll('button')].map((b) => b.textContent);
  out.tabs = tabs;
  check(tabs.length === 6, 'six tabs');
  const addForm = () => $('workspace-body').querySelector('form.workspace-add');
  const setText = (el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); };
  setText(addForm().querySelector('input'), 'water the plants');
  addForm().requestSubmit(); await wait(1000);
  let items = [...$('workspace-body').querySelectorAll('.workspace-list li input')].map((i) => i.value);
  out.tasks = items;
  check(items.includes('water the plants'), 'the new task is listed');
  const tab = (label) => [...$('workspace-tabs').querySelectorAll('button')].find((b) => b.textContent === label);
  tab('Memory').click(); await wait(800);
  setText(addForm().querySelector('input'), 'likes tea');
  addForm().requestSubmit(); await wait(500);
  check([...$('workspace-body').querySelectorAll('.workspace-list li input')].length === 0, 'a memory without a source is not stored');
  const inputs = addForm().querySelectorAll('input');
  setText(inputs[0], 'likes tea'); setText(inputs[1], 'chat');
  addForm().requestSubmit(); await wait(1000);
  out.memory = [...$('workspace-body').querySelectorAll('.workspace-list li')].map((l) => l.textContent.slice(0, 40));
  check($('workspace-body').querySelectorAll('.workspace-list li input').length === 1, 'the memory with a source is stored');
  tab('Tasks').click(); await wait(800);
  [...$('workspace-body').querySelectorAll('.workspace-list li button')].find((b) => b.textContent === 'Delete').click(); await wait(1000);
  check($('workspace-body').querySelectorAll('.workspace-list li input').length === 0, 'the task is deleted');

  tab('Sources').click(); await wait(800);
  const trustInput = $('workspace-body').querySelector('.workspace-list li input');
  setText(trustInput, '0.2');
  [...trustInput.parentElement.querySelectorAll('button')].find((b) => b.textContent === 'Save').click(); await wait(800);
  tab('Sources').click(); await wait(800);
  out.trust = [...$('workspace-body').querySelectorAll('.workspace-list li input')].map((i) => i.value);
  check(out.trust.includes('0.2'), 'the trust value is kept');

  tab('Persona').click(); await wait(800);
  const area = $('workspace-body').querySelector('textarea');
  setText(area, 'MIA is calm and dry.');
  [...$('workspace-body').querySelectorAll('button')].find((b) => b.textContent === 'Save').click(); await wait(800);
  tab('Persona').click(); await wait(800);
  check($('workspace-body').querySelector('textarea').value === 'MIA is calm and dry.', 'the persona is kept');

  tab('Score').click(); await wait(800);
  out.score = [...$('workspace-body').querySelectorAll('.workspace-list li')].map((l) => l.textContent);
  check(out.score.length === 5 && out.score[0].startsWith('Overall') && out.score[0].endsWith('+1'), 'the score shows overall +1 and four categories');
  $('workspace-close').click(); await wait(200);

  // --- account -------------------------------------------------------------------------------------------------------
  $('menu-button').click(); await wait(200);
  $('account-button').click(); await wait(800);
  check($('account-name').textContent === 'anna', 'the account dialog names the account');
  const fill = (id, v) => setText($(id), v);
  fill('account-old', 'pw-anna'); fill('account-new', 'long-enough-1'); fill('account-repeat', 'other');
  $('account-form').requestSubmit(); await wait(300);
  check($('account-error').textContent.includes('not the same'), 'two different new passwords are refused');
  fill('account-repeat', 'long-enough-1'); fill('account-old', 'wrong');
  $('account-form').requestSubmit(); await wait(800);
  check($('account-error').textContent.includes('current password is wrong'), 'a wrong current password is told');
  fill('account-old', 'pw-anna');
  $('account-form').requestSubmit(); await wait(800);
  check(!$('account').open, 'the dialog closes after a change');
  return JSON.stringify(out, null, 1);
})()
