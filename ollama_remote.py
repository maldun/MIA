"""Ollama that is not started by MIA (a compose service, another machine): wait until it answers and pull the missing models through its API."""
import time

from ollama import Client


def ollama_url(cfg):
    """the address of Ollama: 'ollama_host' (a full URL) if set, else protocol://address:port"""
    host = cfg.get("ollama_host")
    if host:
        return str(host).rstrip("/")
    return "%s://%s:%s" % (cfg.get("protocol", "http"), cfg.get("address", "localhost"), cfg.get("port", 11434))


def wait_for_ollama(client, timeout=120, pause=2, sleep=time.sleep, now=time.monotonic):
    """True as soon as the server answers, False after timeout seconds"""
    end = now() + timeout
    while True:
        try:
            client.list()
            return True
        except Exception:
            if now() >= end:
                return False
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


def prepare(cfg, timeout=None, log=print, client=None):
    """wait for the server, then pull version and version_light if missing. True if Ollama was reachable."""
    client = client or Client(host=ollama_url(cfg))
    if not wait_for_ollama(client, timeout=cfg.get("ollama_wait", 300) if timeout is None else timeout):
        log("Ollama at %s does not answer" % ollama_url(cfg))
        return False
    pull_missing(client, [cfg.get("version"), cfg.get("version_light")], log=log)
    return True
