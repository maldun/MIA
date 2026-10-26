#!/usr/bin/env python3
"""
Accounts of MIA on the command line (the owner's tool; the page cannot create the first account).

  python3 tools/accounts_cli.py create NAME            asks for the password twice (not shown), stores only its scrypt hash
  python3 tools/accounts_cli.py password NAME          a new password for an existing account
  python3 tools/accounts_cli.py list                   the names
  options: --dir data/db   the folder of the file storage (config key accounts_dir)

The password is never an argument (it would show in the process list and the shell history). Turn the login on with "accounts_enabled": true and name
the owner in "owner_account" in setup_cfg.json. Standard library only.
"""
import argparse
import getpass
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import accounts                                        # noqa: E402
from storage import Storage                            # noqa: E402
from storage_files import FileBackend                  # noqa: E402

MIN_PASSWORD = 8


def run(args, ask=getpass.getpass, show=print):
    store = Storage(FileBackend(args.dir))
    if args.command == "list":
        show("\n".join(sorted(store.ids("accounts"))) or "no accounts")
        return 0
    password = ask("Password for %s: " % args.name)
    if len(password) < MIN_PASSWORD:
        show("at least %d characters" % MIN_PASSWORD)
        return 1
    if password != ask("Again: "):
        show("the two passwords differ")
        return 1
    try:
        (accounts.create if args.command == "create" else accounts.set_password)(store, args.name, password, "owner")
    except ValueError as exc:
        show(str(exc))
        return 1
    except Exception as exc:                          # a missing account for `password` comes from the storage
        show("failed: %s" % exc)
        return 1
    show("%s: %s" % ("created" if args.command == "create" else "password changed", args.name))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["create", "password", "list"])
    parser.add_argument("name", nargs="?")
    parser.add_argument("--dir", default=os.path.join(os.path.dirname(HERE), "data", "db"))
    args = parser.parse_args(argv)
    if args.command != "list" and not args.name:
        parser.error("name the account")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
