// Voice check for browser_check.py --eval (needs ui/tools/chat_stub_server.py running):
//   python ui/tools/browser_check.py "http://127.0.0.1:8685/?character=0" shot.png --eval "$(cat ui/tools/chat_audio_e2e.js)"
// Two lines are uploaded one right after the other (the second arrives while the first plays), like the speech process does; a second
// page (another socket) is connected as well. Checks: both lines play one after the other, only this page gets them, the talking state
// ends, no line is lost.
(async () => {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const out = { events: [], speaking: [] };
  const audio = document.getElementById('audio');
  for (const name of ['playing', 'ended', 'error', 'pause', 'emptied']) audio.addEventListener(name, () => out.events.push(name));
  const original = window.miaChat.character.speaking;
  window.miaChat.character.speaking = (value) => { out.speaking.push(value); original(value); };

  // a second page: it never claims the voice
  const { io } = await import('/static/vendor/socket.io.esm.min.js');
  const other = io(location.origin);
  let otherLines = 0;
  other.on('audio_reload', () => { otherLines += 1; });
  await new Promise((resolve) => other.on('connect', resolve));
  await wait(500);

  function wav(seconds, hz) {
    const rate = 8000, n = Math.floor(rate * seconds), buffer = new ArrayBuffer(44 + n * 2), v = new DataView(buffer);
    const text = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
    text(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); text(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
    v.setUint16(22, 1, true); v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    text(36, 'data'); v.setUint32(40, n * 2, true);
    for (let i = 0; i < n; i += 1) v.setInt16(44 + i * 2, Math.sin(2 * Math.PI * hz * i / rate) * 8000, true);
    return new Blob([buffer], { type: 'audio/wav' });
  }
  async function upload(seconds, hz, name) {
    const form = new FormData();
    form.append('file', wav(seconds, hz), name);
    return (await fetch('/upload', { method: 'POST', body: form })).status;
  }

  out.upload1 = await upload(1.0, 440, 'a.wav');
  await wait(200);
  out.upload2 = await upload(0.8, 660, 'b.wav');         // arrives while the first line is still playing
  out.queuedWhilePlaying = window.miaChat.sound.queued;
  const start = Date.now();
  while (Date.now() - start < 6000 && (window.miaChat.sound.playing || window.miaChat.sound.queued || out.events.filter((e) => e === 'ended').length < 2)) await wait(100);
  await wait(500);
  out.played = out.events.filter((e) => e === 'playing').length;
  out.ended = out.events.filter((e) => e === 'ended').length;
  out.errors = out.events.filter((e) => e === 'error').length;
  out.otherPageGotLines = otherLines;
  out.speakingNow = window.miaChat.sound.playing;
  out.speakingCalls = out.speaking.join(',');
  out.lastSpeaking = out.speaking[out.speaking.length - 1];
  out.queueEmpty = window.miaChat.sound.queued === 0;
  return JSON.stringify(out);
})()
