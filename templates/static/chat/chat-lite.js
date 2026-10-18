// Temporary message list for C1: user bubbles, typing dots, MIA's answers from the old `answer` event.
// C2/C3 replace it with the real chat protocol (chat log, history, streaming, queue).

export function isNearBottom(element, threshold = 80) {
  return element.scrollHeight - element.scrollTop - element.clientHeight <= threshold;
}

export function initChatLite({ list, empty, jump, render, t, win = window }) {
  let pending = null; // MIA bubble waiting for the answer to the last message
  let stick = true;

  function scrollDown() {
    list.scrollTop = list.scrollHeight;
    jump.hidden = true;
  }

  function added() {
    empty.hidden = true;
    if (stick) win.requestAnimationFrame(scrollDown);
    else jump.hidden = false;
  }

  function bubble(role) {
    const element = document.createElement('div');
    element.className = `msg ${role}`;
    list.append(element);
    return element;
  }

  function typing() {
    const element = bubble('assistant');
    element.setAttribute('aria-label', '...');
    element.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
    return element;
  }

  function fill(element, text) {
    element.classList.add('md');
    element.innerHTML = render(text);
  }

  list.addEventListener('scroll', () => {
    stick = isNearBottom(list);
    if (stick) jump.hidden = true;
  });
  jump.addEventListener('click', () => {
    stick = true;
    scrollDown();
  });

  return {
    user(text) {
      bubble('user').textContent = text;
      pending ??= typing();
      stick = true;
      added();
    },
    answer(text) {
      const element = pending ?? bubble('assistant');
      pending = null;
      element.removeAttribute('aria-label');
      fill(element, text);
      added();
    },
    note(text) {
      bubble('note').textContent = text;
      added();
    },
  };
}
