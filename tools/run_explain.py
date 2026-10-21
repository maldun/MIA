#!/usr/bin/env python
"""Looking at what a run did: python tools/run_explain.py list | show | explain | cost | problems | diff | export | call | reproduce  (see run_explain.py in the MIA folder)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_explain import main                             # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
