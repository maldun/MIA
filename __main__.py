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
import json
import os
import signal
import subprocess
import threading
from .web_app import socketio, app, port, comm

from .constants import CFG_FILE, LOG_FNAME
fpath = os.path.split(__file__)[0]
cfg_file = os.path.join(fpath,CFG_FILE)
exchange_file = os.path.join(fpath,"exchange.txt")
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
static_folder = os.path.join(fpath,STATIC_DIR)

with open(cfg_file,'r') as jp:
    cfg = json.load(jp)

if __name__ == "__main__":
    try:
        lock = threading.Lock()
        cmd = ["python3.10",os.path.join(fpath,"speak.py"),cfg_file,exchange_file]
        with lock:
            proc = subprocess.Popen(cmd)
        comm.calibrate()
        socketio.run(app, debug=False,port=port)
    except KeyboardInterrupt:
        comm.dump_history()
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        if os.path.exists(exchange_file):
            os.remove(exchange_file)
        
