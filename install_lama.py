import argparse
import json
import subprocess
import time
import os
import sys

parser = argparse.ArgumentParser(
                  prog='install_ollama',
                  description='Installs ollama docker',
                  epilog='Setup setup_cfg.json first!')

parser.add_argument('cfg_file')           # positional argument
#parser.add_argument('-c', '--count')      # option that takes a value
# parser.add_argument('-f', '--first_setup',action='store_true')  # on/off flag

args = parser.parse_args()

CFG_FILE = "setup_cfg.json"
if len(args.cfg_file) > 0:
  cfg_file = args.cfg_file
else:
  cfg_file = CFG_FILE
  
# first_setup = args.first_setup

# Note: It may be necessary to reset before if docker makes problem ... 
# e.g. with podman do `podman system reset`

def install_ollama(name="ollama",version="llama3.2",docker="docker",mode="rocm",port=11434,timeout=10,gfx_version=None,**_):
    cmd = [docker]
    if mode == "rocm":
      # label=disable: SELinux (Fedora) otherwise makes the ROCm runtime crash when loading a model
      cmd +=  "run --replace -d --device /dev/kfd --device /dev/dri --security-opt label=disable".split()
      # needed for cards like the RX 7800 XT (gfx1101), same setting as for torch in speak.py
      if gfx_version is not None:
        cmd += ["-e", f"HSA_OVERRIDE_GFX_VERSION={gfx_version}"]
      # keep the VRAM footprint small: one model at a time, one slot (no extra KV cache)
      cmd += ["-e", "OLLAMA_MAX_LOADED_MODELS=1", "-e", "OLLAMA_NUM_PARALLEL=1"]
      cmd += f"-v ollama:/root/.ollama -p {port}:{port} --name {name} ollama/ollama:rocm".split()
    elif mode == "cpu":
      cmd += f"run --replace -d -v ollama:/root/.ollama -p {port}:{port} --name {name} ollama/ollama".split()
      
    proc = subprocess.Popen(cmd)
    proc.wait()

# Note: only downloads the models; `ollama run` would load the model into the GPU (VRAM) right away
def start_ollama(version="lama3.2",version_light=None,docker="docker",timeout=10,mode="rocm",port=11434,name="ollama",**_):
    for model in [version,version_light]:
        if model is None:
            continue
        cmd = [docker] + f"exec {name} ollama pull".split() + [model]
        proc = subprocess.Popen(cmd)
        proc.wait()

if __name__ == "__main__":
    with open(cfg_file,'r') as fp:
        cfg = json.load(fp)
    install_ollama(**cfg)
    #if first_setup is True:
    start_ollama(**cfg)
