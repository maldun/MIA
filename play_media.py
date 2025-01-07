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


import numpy as np
import cv2
import subprocess
import os
from playsound import playsound



filename = 'wave001.avi'
delay = 25

def play_animation_cv2(filename,window_name,delay=delay):
    cap = cv2.VideoCapture(filename)

    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret:
            color_setting = cv2.cvtColor(frame, cv2.COLOR_RGB2XYZ)

            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            cv2.imshow(window_name,color_setting)
            
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def play_animation_mplayer(filename,window_name,delay=delay):
    with open(os.devnull, 'w') as FNULL:
        p = subprocess.run(["mplayer","-title",window_name,"-speed",str(delay), filename],stdout=FNULL, stderr=subprocess.STDOUT)
        if p.returncode is 0:
            return True
        else:
            return False

def play_animation(filename,window_name,delay=delay):
    """
    Animation player meta function
    """
    return play_animation_mplayer(filename,window_name,delay=delay)

def play_sound(filename):
    playsound(filename)


