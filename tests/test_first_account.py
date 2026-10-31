"""TC-OPR-002 / REQ-OPR-002
Run with: python tests/test_first_account.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                         # noqa: E402
import first_account                             # noqa: E402
import accounts                                  # noqa: E402
from storage import Storage                      # noqa: E402
from storage_files import FileBackend            # noqa: E402

TOOL = os.path.join(REPO, "tools", "accounts_cli.py")


class FirstAccountOffer(unittest.TestCase):
    """first_account.offer at the start of `python -m MIA`, on a temporary data folder with a real (empty) file store of accounts."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = os.path.join(self.tmp.name, "data")
        self.accounts = os.path.join(self.data, "db")
        os.makedirs(self.accounts)
        self.shown = []
        self.asked = []
        self.runs = []

    def ask(self, answer):
        """a stand-in for input() that records the question and gives the answer"""
        def ask(question):
            self.asked.append(question)
            return answer
        return ask

    def offer(self, terminal, answer=""):
        """runs first_account.offer with recording stand-ins; gives its return value"""
        return first_account.offer(self.data, self.accounts, terminal=terminal, ask=self.ask(answer),
                                   show=self.shown.append, run=self.runs.append)

    @mark.req('REQ-OPR-002')
    def test_the_first_start_without_a_terminal_prints_one_line_and_leaves_the_marker(self):
        """TC-OPR-002: the first start of python -m MIA without a terminal and without an account prints one line with the command and leaves the marker (D-136).

        Example: no account, no terminal -> one line "... python tools/accounts_cli.py create NAME --dir <accounts>", data/first_account_offered exists
        """
        # Given: an empty file store of accounts (setUp)
        # When: the offer runs without a terminal
        result = self.offer(terminal=False)
        # Then: one line with the command, no question, and the marker in the data folder
        self.assertTrue(result)
        self.assertEqual(len(self.shown), 1, self.shown)
        self.assertIn("python tools/accounts_cli.py create NAME --dir " + self.accounts, self.shown[0])
        self.assertEqual(self.asked, [])
        self.assertTrue(os.path.exists(os.path.join(self.data, first_account.MARKER)))

    @mark.req('REQ-OPR-002')
    def test_the_second_start_stays_quiet_even_without_an_account(self):
        """TC-OPR-002: after the first offer a later start offers nothing, even when no account was made (D-136).

        Example: offer once, then start again on a terminal -> nothing shown, nothing asked, nothing run
        """
        # Given: the first start has offered the account
        self.offer(terminal=False)
        self.shown.clear()
        # When: MIA starts again on a terminal
        result = self.offer(terminal=True, answer="anna")
        # Then: no offer
        self.assertFalse(result)
        self.assertEqual(self.shown, [])
        self.assertEqual(self.asked, [])
        self.assertEqual(self.runs, [])

    @mark.req('REQ-OPR-002')
    def test_a_name_typed_on_a_terminal_creates_the_owner_account(self):
        """TC-OPR-002: on a terminal the first start asks for the owner's name and runs the account tool with it.

        Example: answer "anna" -> accounts_cli.py create anna --dir <accounts>
        """
        # Given: an empty file store of accounts (setUp)
        # When: the offer runs on a terminal and the owner types a name
        result = self.offer(terminal=True, answer="anna")
        # Then: one question, and the account tool creates that account
        self.assertTrue(result)
        self.assertEqual(len(self.asked), 1, self.asked)
        self.assertIn("Name (empty = later)", self.asked[0])
        self.assertEqual(self.runs, [[sys.executable, TOOL, "create", "anna", "--dir", self.accounts]])

    @mark.req('REQ-OPR-002')
    def test_an_empty_answer_leaves_it_for_later(self):
        """TC-OPR-002: an empty answer makes no account; the line with the command is printed and the marker is left.

        Example: answer "  " -> no run, one line with the command, marker exists
        """
        # Given: an empty file store of accounts (setUp)
        # When: the owner answers with nothing on a terminal
        result = self.offer(terminal=True, answer="  ")
        # Then: no account tool run, the command shown once, and the marker left
        self.assertTrue(result)
        self.assertEqual(self.runs, [])
        self.assertEqual(len(self.shown), 1, self.shown)
        self.assertIn("accounts_cli.py create NAME", self.shown[0])
        self.assertTrue(os.path.exists(os.path.join(self.data, first_account.MARKER)))

    @mark.req('REQ-OPR-002')
    def test_no_offer_when_an_account_exists(self):
        """TC-OPR-002: a start with an account in the file store offers nothing and leaves no marker.

        Example: account anna exists -> nothing asked or shown, no marker
        """
        # Given: the account anna in the file store
        accounts.create(Storage(FileBackend(self.accounts)), "anna", "pw-anna-12345", "owner")
        # When: MIA starts on a terminal
        result = self.offer(terminal=True, answer="bob")
        # Then: no offer and no marker
        self.assertFalse(result)
        self.assertEqual(self.asked, [])
        self.assertEqual(self.shown, [])
        self.assertFalse(os.path.exists(os.path.join(self.data, first_account.MARKER)))

class MiaOffersAtStart(unittest.TestCase):
    """__main__.py imports the whole app, so its wiring is checked in the source (as test_missing_options does)."""

    @mark.req('REQ-OPR-002')
    def test_mia_offers_the_first_account_before_the_helpers_start(self):
        """TC-OPR-002 (D-136): python -m MIA calls first_account.offer with the data folder and the accounts folder of the config, before the server starts.

        Example: __main__.py has "first_account.offer(" before "subprocess.Popen(cmd_llama)".
        """
        # Given: the start code of MIA
        with open(os.path.join(REPO, "__main__.py"), encoding="utf-8") as fp:
            source = fp.read()
        # When: the call of the offer is looked for
        at = source.find("first_account.offer(")
        # Then: it is there, with the accounts folder of the config, and before the helpers and the server start
        self.assertGreater(at, 0)
        self.assertIn("ACCOUNTS_DIR_KEY", source[at:at + 300])
        self.assertLess(at, source.find("subprocess.Popen(cmd_llama)"))


if __name__ == '__main__':
    unittest.main()
