"""
The secret between MIA's own processes (N-2.1 T-02, REQ-API-007).

With the accounts switched on every request needs a session. The speech process posts the finished audio to /upload and the scheduler asks /time; they have no
session. web_app.py makes a random secret at start (environment variable MIA_INTERNAL_TOKEN, inherited by the speech process, which __main__ starts afterwards);
the callers send it in the header X-MIA-Internal, and the guard lets exactly the internal paths pass with it. Nothing else opens with it.
Standard library only (the speech process imports this without flask).
"""
import os
import secrets

INTERNAL_ENV = "MIA_INTERNAL_TOKEN"
INTERNAL_HEADER = "X-MIA-Internal"


def ensure_token():
    """the secret of this MIA start; made once, kept in the environment for the processes started afterwards"""
    return os.environ.setdefault(INTERNAL_ENV, secrets.token_hex(16))


def internal_headers():
    """headers for a call to our own web server: the secret if there is one (no secret, no header, as before the accounts)"""
    token = os.environ.get(INTERNAL_ENV)
    return {INTERNAL_HEADER: token} if token else {}
