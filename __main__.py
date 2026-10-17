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
from .web_app import socketio, app, comm, WEB_PORT, scheduler, time_update_trigger
from .utils import get_own_ip
from .tls_proxy import start_https_proxy
from .constants import HTTPS_PORT_KEY
from .shutdown import install_term_handler, stop_process, graceful_shutdown, DEFAULT_PAUSE

from .constants import CFG_FILE, LOG_FNAME
fpath = os.path.split(__file__)[0]
cfg_file = os.path.join(fpath,CFG_FILE)
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
static_folder = os.path.join(fpath,STATIC_DIR)

with open(cfg_file,'r') as jp:
    cfg = json.load(jp)

if __name__ == "__main__":
    https_proc = None
    speak_proc = None
    # Ctrl+C, SIGTERM and the commands /break! and /goodnight! all end in the same orderly shutdown below
    install_term_handler()
    try:
        cmd_speak = ["python3.10",os.path.join(fpath,"speak.py"),cfg_file]
        cmd_llama = ["python3.10",os.path.join(fpath,"install_lama.py"),cfg_file]
        
        lock = threading.Lock()
        with lock:
            llama_proc = subprocess.Popen(cmd_llama)
            print(f"llama process started with {llama_proc.pid}")
            # own session: Ctrl+C in the terminal reaches only MIA, which stops the helper in order
            speak_proc = subprocess.Popen(cmd_speak,start_new_session=True)
            print(f"speak process started with {speak_proc.pid}")
            llama_proc.wait()
            print("llama proc finished!")
            
            comm.calibrate()
            # a little trickery ... make the main process pid known ...
            # left here for future reference ...
            #app.config[MAIN_THREAD_ID_KEY] = os.getpid()
            host_ip = get_own_ip()
            #host_ip=None
            # listen on all addresses (localhost and LAN), "host" in the cfg file can restrict this.
            # The character needs a secure context: http://localhost:<web_port> or the https proxy.
            host = cfg.get("host","0.0.0.0")
            https_proc = start_https_proxy(cfg,fpath,WEB_PORT)
            print(f"MIA: http://localhost:{WEB_PORT}")
            if https_proc is not None:
                print(f"MIA (https, for other devices): https://{host_ip}:{cfg[HTTPS_PORT_KEY]}")
            socketio.run(app, host=host,debug=False,port=WEB_PORT)
            
    except KeyboardInterrupt:
        print("MIA is shutting down ...")
    finally:
        # one step after the other with a short pause, instead of everything at the same instant
        graceful_shutdown([("save history", comm.dump_history),
                           ("stop https proxy", lambda: stop_process(https_proc,"https proxy",group=True)),
                           ("stop speech process", lambda: stop_process(speak_proc,"speech process",group=True))],
                          pause=cfg.get("shutdown_pause",DEFAULT_PAUSE))
        print("MIA stopped.")
