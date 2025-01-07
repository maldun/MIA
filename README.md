==============================
MIA - MIA Is not an Assistant
==============================

    Copyright (C) 2024  Stefan Reiterer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Attempt to create my own virtual assistant. This project can be seen as long term and evolving.
It is not the goal to make state of the art algorithms, but to deepen my understanding of machine learning, by trying out
to automate everyday tasks, and machine communication.

Installation
==================

Install ROCM/CUDA (Fedora):
- `sudo usermod -a -G video $LOGNAME`
- `sudo dnf install rocminfo`
- `sudo dnf install rocm-opencl`
-  `sudo dnf install rocm-clinfo`
- `sudo dnf install rocm-hip`
- `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0`

Source: https://medium.com/@anvesh.jhuboo/rocm-pytorch-on-fedora-51224563e5be



Notes
==================
It may be necessary to reset before if docker makes problem ... e.g. with podman do `podman system reset`
Setup rocm properly and install with `python3.10 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0`
Also set your GLX proeprly, in my case it was: `os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"`

Programm Structure
==================

I now aim to use ollama as a basis.
So a big rewrite is coming ...

Tasks
=====

- Scheduling: One of the main tasks is to provide an efficient work schedule for every day life.
- Communication: Communication with the user
