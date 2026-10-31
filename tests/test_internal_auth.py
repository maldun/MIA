"""
internal_auth.py: the secret between MIA's own processes; the speech process sends it with the audio upload (play_media.play_sound).
Run in the image: bash tools/run_in_image.sh tests/test_internal_auth.py
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import internal_auth as I                             # noqa: E402


class Secret(unittest.TestCase):
    def setUp(self):
        self.saved = os.environ.pop(I.INTERNAL_ENV, None)
        self.addCleanup(lambda: os.environ.pop(I.INTERNAL_ENV, None) or (self.saved and os.environ.__setitem__(I.INTERNAL_ENV, self.saved)))

    def test_without_a_secret_there_is_no_header(self):
        """Without the internal secret in the environment, our own processes send no secret header.

        Example: no MIA_INTERNAL_TOKEN -> internal_headers() is {}.
        """
        self.assertEqual(I.internal_headers(), {})

    def test_the_secret_is_made_once_and_is_what_the_headers_carry(self):
        """The internal secret is made once per start, at least 32 characters, and the headers of our own processes carry it.

        Example: ensure_token() twice -> the same token; internal_headers() -> {X-MIA-Internal: token}.
        """
        # Given / When: the secret is made
        token = I.ensure_token()
        # Then: it is long, the same for a second caller, and the header carries it
        self.assertGreaterEqual(len(token), 32)
        self.assertEqual(I.ensure_token(), token)                                   # the same for every caller of this start
        self.assertEqual(I.internal_headers(), {I.INTERNAL_HEADER: token})

    def test_the_audio_upload_of_the_speech_process_carries_it(self):
        """The speech process uploads its audio with the internal secret in the header, so the guard lets it pass without a session.

        Example: play_sound(a .wav, url .../upload) -> the POST carries {X-MIA-Internal: token}.
        """
        import play_media
        # Given: the secret and a small wav file
        token = I.ensure_token()
        wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav.write(b"RIFF")
        wav.close()
        self.addCleanup(os.remove, wav.name)
        # When: the speech process uploads it (the request is caught)
        with mock.patch.object(play_media.requests, "post") as post:
            post.return_value.text = "ok"
            play_media.play_sound(wav.name, url="http://127.0.0.1:1/upload")
        # Then: the request carries the secret
        self.assertEqual(post.call_args.kwargs["headers"], {I.INTERNAL_HEADER: token})


if __name__ == "__main__":
    unittest.main()
