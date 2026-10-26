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
        self.assertEqual(I.internal_headers(), {})

    def test_the_secret_is_made_once_and_is_what_the_headers_carry(self):
        token = I.ensure_token()
        self.assertGreaterEqual(len(token), 32)
        self.assertEqual(I.ensure_token(), token)                                   # the same for every caller of this start
        self.assertEqual(I.internal_headers(), {I.INTERNAL_HEADER: token})

    def test_the_audio_upload_of_the_speech_process_carries_it(self):
        import play_media
        token = I.ensure_token()
        wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wav.write(b"RIFF")
        wav.close()
        self.addCleanup(os.remove, wav.name)
        with mock.patch.object(play_media.requests, "post") as post:
            post.return_value.text = "ok"
            play_media.play_sound(wav.name, url="http://127.0.0.1:1/upload")
        self.assertEqual(post.call_args.kwargs["headers"], {I.INTERNAL_HEADER: token})


if __name__ == "__main__":
    unittest.main()
