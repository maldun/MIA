import json
import subprocess
import time
import os
import sys

CFG_FILE = "setup_cfg.json"
if len(sys.argv) > 1:
  cfg_file = sys.argv[1]
else:
  cfg_file = CFG_FILE

# Note: It may be necessary to reset before if docker makes problem ... 
# e.g. with podman do `podman system reset`

def install_ollama(name="ollama",version="llama3.2",docker="docker",mode="rocm",port=11434,timeout=10,**_):
    cmd = [docker]
    if mode == "rocm":
      cmd +=  f"run --replace -d --device /dev/kfd --device /dev/dri -v ollama:/root/.ollama -p {port}:{port} --name {name} ollama/ollama:rocm".split()
    elif mode == "cpu":
      cmd += f"run --replace -d -v ollama:/root/.ollama -p {port}:{port} --name {name} ollama/ollama".split()
    
    proc = subprocess.Popen(cmd)
    proc.wait()

# Note: To stop the dialoge enter /bye in prompt
def start_ollama(version="lama3.2",docker="docker",timeout=10,mode="rocm",port=11434,name="ollama",**_):
    cmd = [docker] + f"exec -it {name} ollama run ".split() + [version]
    proc = subprocess.Popen(cmd)
    time.sleep(timeout)
    proc.communicate(input=b'/bye')
    proc.wait()

if __name__ == "__main__":
    with open(cfg_file,'r') as fp:
        cfg = json.load(fp)
    install_ollama(**cfg)
    #start_ollama(**cfg)
