'''
Created on Jan 17, 2017

@author: radoslav
'''

class Waveform():
    def __init__( self, file, **kwargs ):
        self.file_ = file

    def isReady( self ):
        return True
