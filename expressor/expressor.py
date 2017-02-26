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

# standard messages
interface_string = "Error: This is the prototype interface!"
variant_string = "Error: Variant not implemented!"

def get_current_dir():
    import inspect, os
    #print(inspect.getfile(inspect.currentframe())) # script filename (usually with path))
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

from . import play_media

class ExpressorInterface:
    """
    The expressor main class interface
    """
    def greet(self,variant=0):
        raise NotImplementedError(interface_string)
    
    
class VisualExpressor(ExpressorInterface):
    """
    This is the main class for visual expressions.
    First version using animated videos from blender.
    """
    
    def __init__(self,video_directory,video_name='MIA',delay=1):
        """
        The init method only has to store the directory containing
        the multimedia for videos.
        """
        self.video_directory = video_directory
        self.delay = delay
        self.video_name = video_name
        
    def greet(self,variant=0):
        
        if variant in [0]:
            return play_media.play_animation(self.video_directory+"greet{0:03d}.avi".format(variant),window_name=self.video_name,delay=self.delay)
        else:
            raise NotImplementedError(variant_string)
        
