"""
Accounts with a salted slow password hash (REQ-SLY-005, REQ-DB-005).

The password is never stored or logged: a record of the table `accounts` holds a random salt and the scrypt hash of the standard library, with the
parameters used, so they can be raised later without breaking old accounts. Who may create an account is a rule of the Backend (REQ-BE-011), not of
this module. Login throttling is the job of the API (REQ-API-004).
"""
import hashlib
import hmac
import os

N, R, P = 2 ** 14, 8, 1          # scrypt: about 16 MiB and tens of milliseconds per check
KEY_BYTES = 32


def _hash(password, salt, n, r, p):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=KEY_BYTES, maxmem=128 * n * r * 2)


def _record(password):
    salt = os.urandom(16)
    return {"algorithm": "scrypt", "n": N, "r": R, "p": P, "salt": salt.hex(), "hash": _hash(password, salt, N, R, P).hex()}


def _check_input(name, password):
    if not isinstance(name, str) or not name or not isinstance(password, str) or not password:
        raise ValueError("an account needs a name and a password")


def create(store, name, password, author):
    """A new account; an existing name is a ValueError."""
    _check_input(name, password)
    if name in store.ids("accounts"):
        raise ValueError("the account exists: %s" % name)
    store.put("accounts", name, dict(_record(password), name=name), author)


def set_password(store, name, password, author):
    """A new version of the account with a new salt and hash."""
    _check_input(name, password)
    store.put("accounts", name, dict(_record(password), name=name), author, expected_version=len(store.history("accounts", name)))


def verify(store, name, password):
    """True for the right password; an unknown account costs the same time as a wrong password."""
    try:
        doc = store.get("accounts", name)["doc"]
    except Exception:
        doc = None
    if doc is None or not isinstance(password, str):
        _hash("x", b"\0" * 16, N, R, P)
        return False
    expected = bytes.fromhex(doc["hash"])
    return hmac.compare_digest(_hash(password, bytes.fromhex(doc["salt"]), doc["n"], doc["r"], doc["p"]), expected)
