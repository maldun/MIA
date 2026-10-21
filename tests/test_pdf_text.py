"""
Tests for the PDF converter in its wall (pdf_text.py): text from a small PDF, refusal of what is no PDF, and the wall itself: no files of the machine, no network, no new processes, no
environment, a timeout that kills, a cap on the output. Needs bubblewrap and poppler's pdftotext; without them the wall tests are skipped (and the feature is off, never weakened).
Run with the MIA virtualenv: python tests/test_pdf_text.py
"""
import os
import socket
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import pdf_text as P                                     # noqa: E402

AVAILABLE, WHY = P.available()


def tiny_pdf(lines):
    """a valid one-page PDF with the given lines of text (built by hand, with a correct cross-reference table)"""
    stream = "BT /F1 12 Tf 14 TL 20 180 Td " + " T* ".join("(%s) Tj" % l.replace("(", "\\(").replace(")", "\\)") for l in lines) + " ET"
    objects = ["<</Type/Catalog/Pages 2 0 R>>", "<</Type/Pages/Kids[3 0 R]/Count 1>>",
               "<</Type/Page/Parent 2 0 R/MediaBox[0 0 400 200]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
               "<</Length %d>>\nstream\n%s\nendstream" % (len(stream), stream), "<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
    out = b"%PDF-1.4\n"
    offsets = []
    for n, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += ("%d 0 obj\n%s\nendobj\n" % (n, body)).encode("latin-1")
    xref = len(out)
    out += ("xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)).encode()
    for offset in offsets:
        out += ("%010d 00000 n \n" % offset).encode()
    out += ("trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)).encode()
    return out


@unittest.skipUnless(AVAILABLE, "no wall: %s" % WHY)
class Converter(unittest.TestCase):
    def test_text_of_a_small_pdf(self):
        result = P.pdf_to_text(tiny_pdf(["Conclusion", "Canary releases reduced failed releases by 38 percent."]))
        self.assertIn("Canary releases reduced failed releases by 38 percent.", result["text"])
        self.assertEqual(result["pages_read"], 1)
        self.assertFalse(result["truncated"])
        self.assertLess(result["seconds"], 10)

    def test_parentheses_and_umlauts_survive(self):
        result = P.pdf_to_text(tiny_pdf(["Gr\\366bner bases (a tool)"]))
        self.assertIn("(a tool)", result["text"])

    def test_the_text_is_cut_at_the_limit(self):
        result = P.pdf_to_text(tiny_pdf(["A line of text that is longer than ten characters."]), max_chars=10)
        self.assertEqual(len(result["text"]), 10)
        self.assertTrue(result["truncated"])

    def test_what_is_no_pdf_is_refused(self):
        for junk in (b"", b"hello", b"<html>%PDF-1.4</html>", b"\x00" * 100):
            with self.assertRaises(P.PdfError):
                P.pdf_to_text(junk)
        with self.assertRaises(P.PdfError):
            P.pdf_to_text(b"%PDF-1.4\n this is not a real pdf at all \n%%EOF")                  # a header but nothing behind it: the converter says no

    def test_a_pdf_that_is_too_big_is_refused_before_anything_runs(self):
        old = P.MAX_INPUT_BYTES
        P.MAX_INPUT_BYTES = 100
        try:
            with self.assertRaises(P.PdfError) as caught:
                P.pdf_to_text(b"%PDF-1.4\n" + b"x" * 200)
            self.assertIn("larger than", str(caught.exception))
        finally:
            P.MAX_INPUT_BYTES = old

    def test_a_path_works_like_bytes(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fp:
            fp.write(tiny_pdf(["From a file."]))
        try:
            self.assertIn("From a file.", P.pdf_to_text(fp.name)["text"])
        finally:
            os.remove(fp.name)


@unittest.skipUnless(AVAILABLE, "no wall: %s" % WHY)
class TheWall(unittest.TestCase):
    def run_cmd(self, *argv, **kwargs):
        return P.run_in_wall(list(argv), kwargs.pop("files", {}), **kwargs)

    def test_the_files_of_the_machine_are_not_there(self):
        for path in ("/etc/passwd", "/etc/hostname", "/home", "/root", "/var"):
            code, out, err, _ = self.run_cmd("/usr/bin/ls", path)
            self.assertNotEqual(code, 0, path)
            self.assertEqual(out, b"")

    def test_only_the_input_is_visible_and_it_is_read_only(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write(b"secret input")
        try:
            code, out, _, _ = self.run_cmd("/usr/bin/cat", "/tmp/in.txt", files={"in.txt": fp.name})
            self.assertEqual((code, out), (0, b"secret input"))
            code, _, err, _ = self.run_cmd("/usr/bin/rm", "/tmp/in.txt", files={"in.txt": fp.name})
            self.assertNotEqual(code, 0)
            with open(fp.name, "rb") as again:
                self.assertEqual(again.read(), b"secret input")
            code, _, _, _ = self.run_cmd("/usr/bin/touch", "/usr/bin/evil")
            self.assertNotEqual(code, 0)                                                        # /usr is read-only
        finally:
            os.remove(fp.name)

    def test_no_environment_of_ours(self):
        old = os.environ.get("MIA_TEST_SECRET")
        os.environ["MIA_TEST_SECRET"] = "hunter2"
        try:
            code, out, _, _ = self.run_cmd("/usr/bin/env")
        finally:
            if old is None:
                del os.environ["MIA_TEST_SECRET"]
            else:
                os.environ["MIA_TEST_SECRET"] = old
        self.assertNotIn(b"hunter2", out)
        self.assertNotIn(b"HOME", out)

    def test_no_network_not_even_this_machines_localhost(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        try:
            code, out, err, _ = self.run_cmd("/usr/bin/python3", "-I", "-S", "-c",
                                             "import socket\ns = socket.socket()\ns.settimeout(2)\ntry:\n    s.connect(('127.0.0.1', %d))\n    print('CONNECTED')\nexcept OSError as e:\n    print('blocked', e.errno)" % port, timeout=15)
        finally:
            server.close()
        self.assertNotIn(b"CONNECTED", out)
        self.assertIn(b"blocked", out)

    def test_no_new_processes(self):
        code, out, err, _ = self.run_cmd("/usr/bin/python3", "-I", "-S", "-c", "import os\ntry:\n    os.fork()\n    print('FORKED')\nexcept OSError as e:\n    print('refused', e.errno)", timeout=15)
        self.assertNotIn(b"FORKED", out)
        self.assertIn(b"refused", out)

    def test_a_runaway_process_is_killed_at_the_timeout(self):
        started = time.monotonic()
        code, out, err, seconds = self.run_cmd("/usr/bin/sleep", "30", timeout=1)
        self.assertIsNone(code)
        self.assertLess(time.monotonic() - started, 8)

    def test_far_too_much_output_is_stopped(self):
        code, out, err, seconds = self.run_cmd("/usr/bin/yes", timeout=10, max_output=200000)
        self.assertIsNone(code)
        self.assertLessEqual(len(out), 200000)
        self.assertLess(seconds, 9)


class WithoutAWall(unittest.TestCase):
    def test_the_feature_is_off_not_weakened(self):
        saved = P.tools
        P.tools = lambda: (None, "/usr/bin/pdftotext", None)
        try:
            self.assertEqual(P.available(), (False, "bubblewrap (bwrap) is not installed"))
            with self.assertRaises(P.PdfUnavailable):
                P.pdf_to_text(tiny_pdf(["x"]))
            with self.assertRaises(P.PdfUnavailable):
                P.run_in_wall(["/usr/bin/true"], {})
        finally:
            P.tools = saved
        P.tools = lambda: ("/usr/bin/bwrap", None, None)
        try:
            self.assertFalse(P.available()[0])
        finally:
            P.tools = saved


if __name__ == "__main__":
    unittest.main()
