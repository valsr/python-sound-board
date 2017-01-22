'''
Created on Jan 19, 2017

@author: radoslav
'''
from com.valsr.psb.sound.waveform import Waveform

_WAVEFORMS_ = {}

class WaveformManager:
    def __init__( self, params ):
        '''
        Constructor
        '''
    @staticmethod
    def getPlayer( file ):
        global _WAVEFORMS_
        if id in _WAVEFORMS_:
            return _WAVEFORMS_[file]

        return None

    @staticmethod
    def createWaveform( filePath ):
        global _WAVEFORMS_
        p = Waveform( filePath )
        _WAVEFORMS_[filePath] = p
        return ( filePath, p )

    @staticmethod
    def destroyWaveform( file ):
        global _WAVEFORMS_
        _WAVEFORMS_.pop( file, None )
