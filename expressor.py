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

from abc import ABC, abstractmethod
import json
import os
from .constants import PRESET_KEY, VOICE_KEY, EXPRESSION_FILE
from .play_media import play_sound
from .mia_logger import logger

def get_current_dir():
    import inspect, os
    #print(inspect.getfile(inspect.currentframe())) # script filename (usually with path))
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

class ExpressorInterface:
    """
    The expressor main class interface
    The expressor manages feelings
    """
    DATA_TYPE_KEY = ""
    
    NOT_PROPER_TYPE_MSG = "Error: expressions is not of the proper data type (a json, filename or a dict)"
    NOT_IMPLEMENTED_MSG = "Error: Method not implemented yet!"
    
    def __init__(self,expressions=EXPRESSION_FILE):
        """
        load all information about expressions
        """
        if isinstance(expressions,str):
            if not os.path.exists(expressions):
                try: # maybe a json ...
                    expressions = json.loads(expressions)
                except json.JSONDecodeError:
                    pass
                # let's try if the file is in the same folder
                expressions = os.path.join(get_current_dir(),expressions)
            with open(expressions,'r') as fp:
                expressions = json.load(fp)
        
        if isinstance(expressions,dict):
            # store original for reference (not much data ...)
            self.set_expressions(expressions)
        else:
            raise TypeError(self,NOT_PROPER_TYPE_MSG)
    
    def set_expressions(self,expressions):
        """
        sets the expression dict accordingly ( in this case vids)
        """
        self._expressions = expressions
        for key, val in expressions.items():
            setattr(self,key,val[self.DATA_TYPE_KEY])
    
    @abstractmethod
    def express(self,key):
        """
        Performs action according to need for type
        """
        raise NotImplementedError(self.NOT_IMPLEMENTED_MSG)
        

class PresetExpressor(ExpressorInterface):
    """
    Expresses by telling the 3D character (see ui/) to play an expression preset.
    Replaces the old VideoExpressor: no clips are copied anymore.
    The preset is the "preset" entry of the expression (default: the expression key itself).
    """
    DATA_TYPE_KEY = PRESET_KEY
    UNKNOWN_EXPRESSION_MSG = "Unknown expression {key}, keeping the current one!"

    def __init__(self,expressions=EXPRESSION_FILE,send=None):
        """
        send: function called with the preset name (e.g. emits it to the web page).
        """
        self._send = send
        self.current = None
        super().__init__(expressions)

    def set_expressions(self,expressions):
        self._expressions = expressions
        for key, val in expressions.items():
            setattr(self,key,val.get(self.DATA_TYPE_KEY,key))

    def express(self,key):
        """
        Sends the preset of the expression to the character and returns its name.
        Unknown expressions are logged and ignored, they must not crash MIA.
        """
        if key not in self._expressions:
            logger.error(self.UNKNOWN_EXPRESSION_MSG.format(key=key))
            return None
        preset = getattr(self,key)
        self.current = preset
        if self._send is not None:
            self._send(preset)
        return preset

class VoiceExpressor(ExpressorInterface):
    """
    Class for making expressions in form of voices.
    """
    DATA_TYPE_KEY=VOICE_KEY
    KEY_MISS_ERR = "Error: Expression for voice {key} missing or wrong key!"
    SND_FILE_MISS_ERR = "Error: Sound file {file} is missing! No sound played!"
    DEFAULT_PATH =  os.path.join(get_current_dir(),"voice","expressions")
    def __init__(self,expressions=EXPRESSION_FILE,web_url=None):
        """
        Provided url from webserver for playing sounds.
        """
        self._web_url = web_url
        return super().__init__(expressions=EXPRESSION_FILE)
    
    def express(self,key,fail_on_no_file=False):
        """
        Plays the sound fitting to the expressions
        """
        
        if key not in self._expressions.keys():
            raise KeyError(self.KEY_MISS_ERR.format(key=key))
        sound_file = getattr(self,key)
        if sound_file is None:  # this expression has no voice clip (yet)
            return
        candidates = (sound_file,os.path.join(self.DEFAULT_PATH,sound_file))
        for candidate in candidates:
            if os.path.exists(candidate):
                play_sound(candidate,url=self._web_url)
                break
        else:
            err_msg = self.SND_FILE_MISS_ERR.format(file=sound_file)
            logger.error(err_msg)
            if fail_on_no_file is True:
                raise FileNotFoundError(err_msg)
    
        
