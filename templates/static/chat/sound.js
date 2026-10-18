// MIA's voice: the server writes /audio/out.wav and sends audio_reload; the page plays it.
// Browsers may block autoplay until the first touch/click: then a small button asks for it.

export function initSound({ audio, socket, character, storage, muteToggle, muteLabel, muteIcon, volume, hint, t }) {
  let muted = storage.get('mia.muted') === '1';
  let level = Math.min(100, Math.max(0, Number(storage.get('mia.volume', 100)) || 0));

  function applyAudio() {
    audio.muted = muted;
    audio.volume = level / 100;
    muteToggle.setAttribute('aria-checked', String(muted));
    muteLabel.textContent = t(muted ? 'menu.unmute' : 'menu.mute');
    muteIcon.setAttribute('href', muted ? '#i-volume-off' : '#i-volume');
    volume.value = String(level);
  }

  async function play() {
    try {
      await audio.play();
      hint.hidden = true;
    } catch (error) {
      if (error?.name === 'NotAllowedError') hint.hidden = false;
    }
  }

  audio.addEventListener('playing', () => character.speaking(true));
  audio.addEventListener('pause', () => character.speaking(false));
  audio.addEventListener('ended', () => {
    socket.emit('audio_ended', 'audio playback has ended');
    character.speaking(false);
  });

  socket.on('audio_reload', () => {
    audio.load();
    play();
  });

  muteToggle.addEventListener('click', () => {
    muted = !muted;
    storage.set('mia.muted', muted ? '1' : '0');
    applyAudio();
  });
  volume.addEventListener('input', () => {
    level = Number(volume.value);
    storage.set('mia.volume', level);
    applyAudio();
  });
  hint.addEventListener('click', play);

  applyAudio();
  return { refresh: applyAudio };
}
