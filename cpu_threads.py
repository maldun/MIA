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
The "cpu_threads" setting: how many CPU threads the speech process (onnxruntime for Kokoro,
the BLAS libraries behind numpy) and Ollama's runner may use. Without the setting each of them uses all cores.

This module imports nothing heavy, so the limit can be set before numpy and onnxruntime are imported
(their thread pools are created on import). 0, None, or a missing setting mean: no limit.
"""
import json
import os

CFG_KEY = "cpu_threads"
# thread pools of numpy/scipy/librosa (OpenMP, MKL, OpenBLAS, ...): read when the library is imported
THREAD_ENV_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                   "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")

def parse(value):
    """
    A positive whole number, as number or string, or None (= no limit) for 0, None, empty, negative or invalid values.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        number = int(value) if value.is_integer() else 0
    else:
        try:
            number = int(str(value).strip())
        except ValueError:
            return None
    return number if number > 0 else None

def limit_environment(threads, environ=None):
    """
    Sets the thread environment variables for libraries that are imported afterwards.
    """
    environ = os.environ if environ is None else environ
    if threads:
        for name in THREAD_ENV_VARS:
            environ[name] = str(threads)

def from_config_file(path):
    """
    cpu_threads from a configuration file (None without limit, if unreadable or missing).
    """
    try:
        with open(path, "r") as fp:
            return parse(json.load(fp).get(CFG_KEY))
    except (OSError, ValueError, AttributeError):
        return None

def early_limit_from_argv(argv, default_cfg=None):
    """
    For a script started like `python speak.py setup_cfg.json ...`: reads the setting from the first .json
    file in the arguments (or default_cfg) and sets the environment, before numpy and onnxruntime are imported.
    Returns the number of threads or None.
    """
    candidates = [a for a in argv[1:] if not a.startswith("-") and a.endswith(".json")]
    if default_cfg:
        candidates.append(default_cfg)
    for path in candidates[:1]:
        threads = from_config_file(path)
        limit_environment(threads)
        return threads
    return None

def onnx_session_options(threads):
    """
    onnxruntime options for the thread limit (Kokoro), or None without limit.
    """
    if not threads:
        return None
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    return options

def add_to_llm_options(options, threads):
    """
    Ollama's runner: adds "num_thread" to the model options. An explicit "num_thread" in the options wins,
    without a limit the options stay as they are (also None).
    """
    if not threads:
        return options
    merged = dict(options or {})
    merged.setdefault("num_thread", threads)
    return merged
