#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2024  Stefan Reiterer

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

import logging
import os
import datetime

fpath = os.path.split(__file__)[0]

try:
    from .constants import LOG_FNAME, TIME_FORMAT
except ImportError:
    from constants import LOG_FNAME, TIME_FORMAT

logger = logging.getLogger(__name__)

# Set log level to DEBUG
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

# Create a logging handler that writes logs to a file
handler = logging.FileHandler(os.path.join(fpath,LOG_FNAME))
handler.setLevel(logging.DEBUG)  # Set level here as well
# Formating:
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                              datefmt=TIME_FORMAT)
handler.setFormatter(formatter) 
logger.addHandler(handler)
