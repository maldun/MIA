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
    # if first_setup is True: # download model
    cmd = [docker] + f"exec -it {name} ollama run ".split() + [version] + ['/bye']
    proc = subprocess.Popen(cmd)
    time.sleep(timeout)
    proc.communicate(input='/bye'.encode())
    proc.wait()

if __name__ == "__main__":
    with open(cfg_file,'r') as fp:
        cfg = json.load(fp)
    install_ollama(**cfg)
    #if first_setup is True:
    start_ollama(**cfg)
