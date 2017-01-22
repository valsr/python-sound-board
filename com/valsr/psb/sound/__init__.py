'''
Created on Jan 17, 2017

@author: radoslav
'''
from enum import Enum
from gi.repository import Gst, GObject

class PlayerState( Enum ):
    STOPPED = 1
    PLAYING = 2
    PAUSED = 3
    ERROR = 4
    NOTINIT = 5
    READY = 6

def initAudio():
    GObject.threads_init()
    Gst.init_check( None )
