// Fills and submits the login dialog of the chat page as anna / pw-anna (the accounts of ui/tools/chat_mock_server.py) for ui/tools/cdp_eval.py.
// The page reloads with the session cookie, so the call ends with "Execution context was destroyed": run the next script (for example chat_views_e2e.js) after it.
(async () => {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  document.getElementById('login-user').value = 'anna';
  document.getElementById('login-password').value = 'pw-anna';
  document.getElementById('login-form').requestSubmit();
  await wait(3000);
  return JSON.stringify({ href: location.href });
})()
