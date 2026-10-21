"""Ollama that is not started by MIA (a compose service, another machine): wait until it answers and pull the missing models through its API."""
import os
import time

from ollama import Client


def ollama_url(cfg):
    """the address of Ollama: the environment variable MIA_OLLAMA_HOST, else 'ollama_host' (a full URL), else protocol://address:port"""
    host = os.environ.get("MIA_OLLAMA_HOST") or cfg.get("ollama_host")
    if host:
        return str(host).rstrip("/")
    return "%s://%s:%s" % (cfg.get("protocol", "http"), cfg.get("address", "localhost"), cfg.get("port", 11434))


def wait_for_ollama(client, timeout=120, pause=2, sleep=time.sleep, now=time.monotonic, log=None, every=15, url=""):
    """True as soon as the server answers, False after timeout seconds. While it waits it says so (log) at the start and then every `every` seconds: MIA's page
    only starts after Ollama is there, and a silent wait looks like a hang."""
    start = now()
    end = start + timeout
    last_said = None
    while True:
        try:
            client.list()
            return True
        except Exception as exc:
            if now() >= end:
                return False
            if log is not None and (last_said is None or now() - last_said >= every):
                log("waiting for Ollama%s (%d of %d seconds): %s. The page starts when it answers; start Ollama, or change ollama_host / OLLAMA_URL"
                    % (" at " + url if url else "", now() - start, timeout, type(exc).__name__))
                last_said = now()
            sleep(pause)


def installed_models(client):
    names = set()
    for m in client.list().get("models", []):
        name = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
        if name:
            names.add(name)
    return names


def has_model(names, wanted):
    """'gemma4:26b' matches itself; a name without tag matches 'name:latest'"""
    return wanted in names or (":" not in wanted and wanted + ":latest" in names)


def pull_missing(client, models, log=print):
    """pull every model that is not there yet; returns the list of pulled names"""
    have = installed_models(client)
    pulled = []
    for model in models:
        if not model or has_model(have, model):
            continue
        log("pulling %s ..." % model)
        client.pull(model)
        pulled.append(model)
    return pulled


def prepare(cfg, timeout=None, log=lambda message: print(message, flush=True), client=None):
    """wait for the server, then pull version and version_light if missing. True if Ollama was reachable."""
    client = client or Client(host=ollama_url(cfg))
    if not wait_for_ollama(client, timeout=cfg.get("ollama_wait", 300) if timeout is None else timeout, log=log, url=ollama_url(cfg)):
        log("Ollama at %s does not answer" % ollama_url(cfg))
        return False
    if cfg.get("ollama_pull", True):
        pull_missing(client, [cfg.get("version"), cfg.get("version_light")], log=log)
    else:
        log("ollama_pull is false: the models are not checked")
    return True
