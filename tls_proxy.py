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
Starts the HTTPS proxy (ui/tools/https_proxy.sh) in front of MIA's web app.
The 3D character only runs in a secure context (localhost or HTTPS), so other devices need HTTPS.
"""
import os
import shutil
import subprocess

try:
    from .constants import HTTPS_PORT_KEY
    from .mia_logger import logger
except ImportError:  # used as plain script / in tests
    from constants import HTTPS_PORT_KEY
    from mia_logger import logger

SCRIPT = os.path.join("ui", "tools", "https_proxy.sh")
REQUIRED_TOOLS = ("socat", "openssl")

def start_https_proxy(cfg, folder, web_port, target_host="127.0.0.1"):
    """
    Starts the proxy if "https_port" is set in the configuration.
    Returns the process (stop it with terminate()) or None, if there is no https_port or the proxy cannot run.
    folder: the MIA folder (contains ui/tools/https_proxy.sh).
    """
    https_port = cfg.get(HTTPS_PORT_KEY)
    if not https_port:
        return None
    script = os.path.join(folder, SCRIPT)
    missing = [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]
    if missing:
        logger.error(f"HTTPS proxy not started, missing: {', '.join(missing)} (e.g. sudo dnf install {' '.join(missing)})")
        return None
    if not os.path.exists(script):
        logger.error(f"HTTPS proxy not started, {script} not found")
        return None
    proc = subprocess.Popen([script, str(https_port), f"{target_host}:{web_port}"])
    logger.info(f"HTTPS proxy started (pid {proc.pid}): https port {https_port} -> http {target_host}:{web_port}")
    return proc
