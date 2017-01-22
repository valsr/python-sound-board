'''
Created on Jan 19, 2017

@author: radoslav
'''
from com.valsr.psb.sound.waveform import Waveform

__WAVEFORMS__ = {}

class WaveformManager:
    def __init__( self, params ):
        '''
        Constructor
        '''
    @staticmethod
    def getPlayer( file ):
        global __WAVEFORMS__
        if id in __WAVEFORMS__:
            return __WAVEFORMS__[file]

        return None

    @staticmethod
    def createWaveform( filePath ):
        global __WAVEFORMS__
        p = Waveform( filePath )
        __WAVEFORMS__[filePath] = p
        return ( filePath, p )

    @staticmethod
    def destroyWaveform( file ):
        global __WAVEFORMS__
        __WAVEFORMS__.pop( file, None )
