"""
Created on Jan 17, 2017

@author: valsr <valsr@valsr.com>
"""
import os
from threading import Thread
from enum import Enum
from gi.repository import Gst, GObject
from kivy.logger import Logger


class PlayerState(Enum):
    """Player states"""
    STOPPED = 1
    PLAYING = 2
    PAUSED = 3
    ERROR = 4
    NOTINIT = 5
    READY = 6


def init_audio():
    """Initialize the audio system"""
    GObject.threads_init()
    Gst.init_check(None)
