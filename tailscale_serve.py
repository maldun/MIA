#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Remote access over Tailscale (ui/REQUIREMENTS.md 4.8). `tailscale serve` publishes MIA's web port inside your tailnet with HTTPS and a
certificate of the tailnet (https://<machine>.<tailnet>.ts.net/), no port is opened to the internet. Only devices of your tailnet reach it
(never use `tailscale funnel`, that is public).

This module only calls the `tailscale` command line (nothing else is needed) and is safe without it: every function returns "not available"
when Tailscale is not installed, not running or not logged in. The command runner is a parameter, so tests use a fake.

  tailscale serve --bg <port>                  start (stays after a reboot)
  tailscale serve status                       what is served
  tailscale serve --https=443 <port> off       stop
"""
import json
import shutil
import subprocess

HTTPS_PORT = 443
TIMEOUT = 8


def find_binary():
    return shutil.which("tailscale")


def run(args, timeout=TIMEOUT, binary=None):
    """runs `tailscale <args>`; returns (returncode, output); (None, message) when it cannot run at all"""
    binary = binary or find_binary()
    if binary is None:
        return None, "the tailscale command is not installed"
    try:
        done = subprocess.run([binary] + list(args), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def node_info(runner=run):
    """{"name": "mia.tail1234.ts.net", "state": "Running", "ips": [...]} of this machine, or None (not installed, not running, no login)"""
    code, output = runner(["status", "--json"])
    if code != 0:
        return None
    try:
        data = json.loads(output)
    except ValueError:
        return None
    me = data.get("Self") or {}
    name = str(me.get("DNSName", "")).rstrip(".")
    if not name:
        return None
    return {"name": name, "state": data.get("BackendState", ""), "ips": me.get("TailscaleIPs", []), "online": bool(me.get("Online", True))}


def https_url(name, port=HTTPS_PORT):
    return f"https://{name}/" if port == HTTPS_PORT else f"https://{name}:{port}/"


def origins_for(name):
    """origins of pages that come through `tailscale serve` (the socket and the preset API accept them)"""
    return [f"https://{name}", f"https://{name}:{HTTPS_PORT}", f"http://{name}"] if name else []


def start_serve(port, runner=run):
    """publishes http://127.0.0.1:<port> in the tailnet; returns {"ok", "url", "message"}"""
    info = node_info(runner)
    if info is None:
        return {"ok": False, "url": None, "message": "Tailscale is not available (not installed, not running, or not logged in: sudo tailscale up)"}
    if info["state"] != "Running":
        return {"ok": False, "url": None, "message": f"Tailscale is {info['state'] or 'not running'}, start it with: sudo tailscale up"}
    code, output = runner(["serve", "--bg", str(port)], 30)
    if code != 0:
        # the first call may ask to enable HTTPS certificates in the admin console and prints a link for it
        return {"ok": False, "url": None, "message": "tailscale serve failed: " + output.strip()[:400]}
    return {"ok": True, "url": https_url(info["name"]), "message": "MIA is reachable in your tailnet"}


def stop_serve(port, runner=run):
    code, output = runner(["serve", f"--https={HTTPS_PORT}", str(port), "off"])
    return code == 0


def serve_status(runner=run):
    code, output = runner(["serve", "status"])
    return output.strip() if code is not None else ""
