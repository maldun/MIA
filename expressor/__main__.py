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

import unittest
from .expressor import ExpressorInterface

class ExpressorInterfaceTestCase(unittest.TestCase):
    
    def setUp(self):
        self.expressor = ExpressorInterface()
            
    def test_greet(self):
        with self.assertRaises(NotImplementedError):
            self.expressor.greet()
            
from .expressor import VisualExpressor
from .expressor import get_current_dir

class ExpressorInterfaceTestCase(unittest.TestCase):
    
    def setUp(self):
        self.expressor = VisualExpressor(get_current_dir()+'/vids/')
    def test_greet(self):
        self.assertTrue(self.expressor.greet())

if __name__ == '__main__':
    unittest.main()
