"""
The first account at the first start of `python -m MIA` (REQ-OPR-002, D-136). The page cannot create the first account, so the start offers it once:

  offer(data_dir, accounts_dir)   when the file store of accounts is empty and the offer was never made: on a terminal it asks for the owner's name (empty = later)
                                  and runs tools/accounts_cli.py create NAME; without a terminal it prints one line with that command. Either way it leaves the marker.

The marker is the empty file `first_account_offered` in the data folder (next to the accounts in data/db, and in the stack in the data volume): later starts stay
quiet even when no account was made. `deploy/up.sh` keeps its own marker in deploy/.env. Standard library only.
"""
import os
import subprocess
import sys

MARKER = "first_account_offered"
TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "accounts_cli.py")


def has_accounts(accounts_dir):
    """counted by the account tool, as `deploy/up.sh owner` does (D-136)"""
    listed = subprocess.run([sys.executable, TOOL, "list", "--dir", accounts_dir], capture_output=True, text=True)
    return listed.stdout.strip() != "no accounts"


def offer(data_dir, accounts_dir, terminal=None, ask=input, show=print, run=subprocess.run):
    """offers the owner account once; True when it did"""
    marker = os.path.join(data_dir, MARKER)
    if os.path.exists(marker) or has_accounts(accounts_dir):
        return False
    os.makedirs(data_dir, exist_ok=True)
    open(marker, "w").close()
    if terminal is None:
        terminal = sys.stdin.isatty()
    name = ""
    if terminal:
        try:
            name = ask("No account yet. Make the owner account now? Name (empty = later): ").strip()
        except EOFError:          # Ctrl+D is "later", as up.sh reads it; it must not stop the start (Verify F5)
            pass
    if name and run([sys.executable, TOOL, "create", name, "--dir", accounts_dir]).returncode == 0:
        # the start does not change the configuration; it says how (D-139)
        show('The login is still off: turn it on with "accounts_enabled": true and "owner_account": "%s" in setup_cfg.json.' % name)
    elif name:
        show("The account was not made (see above). Make it when you like:  python tools/accounts_cli.py create NAME --dir %s" % accounts_dir)
    else:
        show("No account yet. Make the owner account when you like:  python tools/accounts_cli.py create NAME --dir %s" % accounts_dir)
    return True
